import datetime
import json
import logging
import os
import typing
import uuid
from dataclasses import (
    dataclass,
    field,
)

from dateutil.parser import parse
from firebase_admin import (
    firestore,
    initialize_app,
)
from flask import (
    Flask,
    Request,
    request,
)
from flask_cors import CORS
from google.cloud import (
    logging as cloud_logging,
    tasks,
)
from google.cloud.firestore import Client
from google.protobuf.timestamp_pb2 import Timestamp
from werkzeug.datastructures import Headers

log_client = cloud_logging.Client()
log_handler = log_client.get_default_handler()
cloud_logger = logging.getLogger("cloudLogger")
cloud_logger.setLevel(logging.INFO)
cloud_logger.addHandler(log_handler)

# Flask setup
app = Flask(__name__)
CORS(app)

# Cloud tasks setup
project_name = os.getenv("GCP_PROJECT")
location = os.getenv("FUNCTION_REGION")
queue = os.getenv("QUEUE_NAME")

client = tasks.CloudTasksClient()
task_queue = client.queue_path(project_name, location, queue)

# Firebase and Firestore setup
firebase_app = initialize_app()
db: Client = firestore.client(firebase_app)


@dataclass
class CalendarTask:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message: str = 'Empty message'
    timestamp: datetime.datetime = None
    timedelta: int = None
    repeat: int = 0

    @property
    def name(self) -> str:
        return 'projects/{project_name}/locations/{location}/queues/{queue}/tasks/{id}'.format(
            project_name=project_name,
            location=location,
            queue=queue,
            id=self.id
        )

    @property
    def callback_url(self) -> str:
        return os.getenv("EVENT_CALLBACK_URL")

    @property
    def service_account_email(self) -> str:
        return os.getenv('SERVICE_ACCOUNT_EMAIL')

    @property
    def schedule_time(self) -> datetime:
        return (self.timestamp or datetime.datetime.now()) + datetime.timedelta(seconds=self.timedelta or 0)

    @property
    def schedule_time_proto(self) -> Timestamp:
        proto_timestamp = Timestamp()
        proto_timestamp.FromDatetime(self.schedule_time)
        return proto_timestamp

    @property
    def payload_dict(self) -> dict:
        return {
            'message': self.message,
            'timedelta': self.timedelta,
            'id': self.id,
            'repeat': self.repeat
        }

    @property
    def payload_blob(self) -> bytes:
        return json.dumps(self.payload_dict).encode('utf-8')

    @property
    def _dict_base(self) -> dict:
        return {
            'name': self.name,
            'http_request': {
                'http_method': 'POST',
                'url': self.callback_url,
                'headers': {
                    "Content-Type": "application/json"
                },
                'oidc_token': {
                    'service_account_email': self.service_account_email
                }
            }
        }

    def to_dict(self) -> dict:
        doc: dict = {
            **self._dict_base,
            'processed': False,
            'execution_counter': 0,
            'schedule_time': self.schedule_time.isoformat(),
        }
        doc['http_request']['body'] = self.payload_dict
        return doc

    def to_task_request(self) -> dict:
        doc: dict = {
            **self._dict_base,
            'schedule_time': self.schedule_time_proto
        }
        doc['http_request']['body'] = self.payload_blob
        return doc


def calendar_api(api_request: Request):
    """Cloud function entry point

    :param api_request: http request
    """
    with app.app_context():

        # construct headers
        headers = Headers()
        for key, value in api_request.headers.items():
            headers.add(key, value)

        # prepare content
        content = {}
        if headers.get('content-type') == 'application/json':
            content['json'] = api_request.get_json(silent=True)
        else:
            content['data'] = api_request.form

        with app.test_request_context(
                method=api_request.method,
                base_url=api_request.base_url,
                path=api_request.path,
                query_string=api_request.query_string,
                headers=headers,
                **content
        ):
            try:
                rv = app.preprocess_request()
                if rv is None:
                    rv = app.dispatch_request()
            except Exception as e:
                rv = app.handle_user_exception(e)
            response = app.make_response(rv)
            return app.process_response(response)


def bad_request(err: str) -> typing.Tuple[dict, int]:
    """Processes bad request on API

    :param err: string message
    :return: error response and status code
    """
    logging.warning({
        "message": "Failed to process API request",
        "error": err
    })
    return dict(error=err), 503


@app.route('/', methods=['GET'])
def get_calendar_events():
    """Returns all calendar events from firestore

    :returns: list of all calendar events
    """
    logging.info({
        "method": request.method,
        "endpoint": request.endpoint,
    })
    response = {
        'objects': [doc.to_dict() for doc in db.collection('events').stream()]
    }
    return response, 200


@app.route('/', methods=['POST'])
def create_calendar_event():
    """Creates new calendar event

    Accepts following json request attributes:
    - message: string message of the calendar event
    - timestamp: RFC 3339 timestamp (ISO format) of when the event is happening
    - timedelta: number of seconds that must pass until the event is triggered
    - repeat: number of times the event will repeat after the set timedelta

    timestamp and timedelta are mutually exclusive
    periodic is used only for timedelta events

    :return: newly created calendar event
    """

    def check_timestamp(value):
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError('Must be a string')
        return parse(value)

    request_json = request.get_json(silent=True)
    logging.info({
        "method": request.method,
        "endpoint": request.endpoint,
        "request": request_json
    })

    message = request_json.get('message', "Empty Message")

    try:
        timestamp = check_timestamp(request_json.get('timestamp'))
        if timestamp and timestamp <= datetime.datetime.now():
            return bad_request("Invalid timestamp (must be a future timestamp)")
    except Exception as ex:
        return bad_request("Invalid timestamp ({})".format(str(ex)))

    timedelta = request_json.get('timedelta')
    if timedelta is not None and not isinstance(timedelta, int):
        return bad_request("Invalid timedelta (Must be an integer)")

    repeat = request_json.get('repeat')
    if repeat is not None and not isinstance(repeat, int):
        return bad_request("Invalid repeat (Must be an integer)")

    if not timedelta and not timestamp:
        return bad_request("at least one of timestamp and timedelta must be set")

    # create new task
    task = CalendarTask(
        timestamp=timestamp,
        timedelta=timedelta,
        repeat=repeat,
        message=message
    )
    task_dict = task.to_dict()
    db.collection('events').document(task.id).set(task_dict)
    client.create_task(
        parent=task_queue,
        task=task.to_task_request()
    )
    return task_dict, 201
