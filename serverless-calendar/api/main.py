import logging
import typing

from firebase_admin import (
    firestore,
    initialize_app,
)
from flask import (
    Flask,
    Request,
    request,
)
from google.cloud import (
    logging as cloud_logging,
)
from google.cloud.firestore import Client

from utils import cloud_function_entry_point

log_client = cloud_logging.Client()
log_handler = log_client.get_default_handler()
cloud_logger = logging.getLogger("cloudLogger")
cloud_logger.setLevel(logging.INFO)
cloud_logger.addHandler(log_handler)

# Flask setup
app = Flask(__name__)


# CORS(app)


# Cloud tasks setup
# client = tasks.CloudTasksClient()
# task_queue = client.queue_path(
#     project=os.getenv("GCP_PROJECT"),
#     location=os.getenv("FUNCTION_REGION"),
#     queue=os.getenv("QUEUE_NAME")
# )

# Firebase and Firestore setup
class FirebaseManager:

    def __init__(self):
        self.firebase_app = initialize_app()
        self.fs_client: Client = firestore.client(self.firebase_app)


db = FirebaseManager()


def calendar_api(api_request: Request):
    """Cloud function entry point

    :param api_request: http request
    """
    return cloud_function_entry_point(app, api_request=api_request)


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
        doc.to_dict()
        for doc in db.fs_client.collection('events').stream()
    }
    return response, 200

#
# @app.route('/', methods=['POST'])
# def create_calendar_event():
#     """Creates new calendar event
#
#     Accepts following json request attributes:
#     - message: string message of the calendar event
#     - timestamp: RFC 3339 timestamp (ISO format) of when the event is happening
#     - timedelta: number of seconds that must pass until the event is triggered
#     - repeat: number of times the event will repeat after the set timedelta
#
#     timestamp and timedelta are mutually exclusive
#     periodic is used only for timedelta events
#
#     :return: newly created calendar event
#     """
#
#     def check_timestamp(value):
#         if value is None:
#             return None
#         if not isinstance(value, str):
#             raise ValueError('Must be a string')
#         return parse(value)
#
#     request_json = request.get_json(silent=True)
#     logging.info({
#         "method": request.method,
#         "endpoint": request.endpoint,
#         "request": request_json
#     })
#
#     message = request.get('message', "Empty Message")
#
#     try:
#         timestamp = check_timestamp(request_json.get('timestamp'))
#         if timestamp <= datetime.datetime.now():
#             return bad_request("Invalid timestamp (must be a future timestamp)")
#     except Exception as ex:
#         return bad_request("Invalid timestamp ({})".format(str(ex)))
#
#     timedelta = request.get('timedelta')
#     if timedelta is not None and not isinstance(timedelta, int):
#         return bad_request("Invalid timedelta (Must be an integer)")
#
#     repeat = request.get('repeat')
#     if repeat is not None and not isinstance(repeat, int):
#         return bad_request("Invalid repeat (Must be an integer)")
#
#     if timestamp and timedelta:
#         return bad_request("timestamp and timedelta are mutually exclusive")
#
#     if not timedelta and not timedelta:
#         return bad_request("one of timestamp and timedelta must be set")
#
#     # create new task
#     task_id = str(uuid.uuid4())
#     schedule_time = datetime.datetime.now() + datetime.timedelta(seconds=timedelta)
#     proto_timestamp = timestamp_pb2.Timestamp()
#     proto_timestamp.FromDateTime(schedule_time)
#     task = {
#         'http_request': {
#             'http_method': 'POST',
#             'url': os.getenv("EVENT_CALLBACK_URL"),
#             'oidc_token': {
#                 'service_account_email': os.getenv('SERVICE_ACCOUNT_EMAIL')
#             },
#             'body': {
#                 'message': message,
#                 'timedelta': timedelta,
#                 'id': task_id,
#                 'repeat': repeat
#             },
#             'name': task_id
#         }
#     }
#     task_doc = {
#         'processed': False,
#         'schedule_time': schedule_time.isoformat(),
#         **task,
#     }
#     db.fs_client.collection('events').document(task_id).set(task_doc)
#     # response = client.create_task(
#     #     parent=task_queue,
#     #     task={
#     #         'schedule_time': proto_timestamp,
#     #         **task,
#     #     }
#     # )
#     # print(response)
#     return task_doc, 201
