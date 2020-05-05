import datetime
import json
import logging
import os
from dataclasses import dataclass

from firebase_admin import (
    firestore,
    initialize_app,
)
from flask import Request
from google.cloud import tasks
from google.cloud.firestore import DocumentReference
from google.cloud.firestore_v1.transaction import (
    Transaction,
    transactional,
)
from google.protobuf.timestamp_pb2 import Timestamp
from slack import WebClient

# prepare slack client
slack_api_token = os.getenv('SLACK_API_TOKEN')
slack_channel = os.getenv("SLACK_CHANNEL")
if not (slack_api_token and slack_channel):
    slack_client = None
else:
    slack_client = WebClient(token=slack_api_token)

# Firebase and Firestore setup
firebase_app = initialize_app()
db = firestore.client(firebase_app)

# Cloud tasks setup
project_name = os.getenv("GCP_PROJECT")
location = os.getenv("FUNCTION_REGION")
queue = os.getenv("QUEUE_NAME")

client = tasks.CloudTasksClient()
task_queue = client.queue_path(project_name, location, queue)


@dataclass
class CalendarTask:
    id: str = None
    message: str = None
    timedelta: int = None
    repeat: int = None

    @property
    def name(self) -> str:
        return 'projects/{project_name}/locations/{location}/queues/{queue}/tasks/{id}_{count}'.format(
            project_name=project_name,
            location=location,
            queue=queue,
            id=self.id,
            count=self.repeat
        )

    @property
    def callback_url(self) -> str:
        return os.getenv("EVENT_CALLBACK_URL")

    @property
    def service_account_email(self) -> str:
        return os.getenv('SERVICE_ACCOUNT_EMAIL')

    @property
    def schedule_time_proto(self) -> Timestamp:
        proto_timestamp = Timestamp()
        proto_timestamp.FromDatetime(datetime.datetime.now() + datetime.timedelta(seconds=self.timedelta))
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

    def to_task_request(self) -> dict:
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
                },
                'body': self.payload_blob
            },
            'schedule_time': self.schedule_time_proto
        }


def calendar_event_callback(request: Request):
    """Processes given calendar event

    :param request: API request
    :returns: empty response + status code
    """
    if not request.data:
        logging.error({
            "message": "Task without data"
        })
        return

    # load task payload data
    request_json = json.loads(request.data)
    task_id = request_json.get('id')
    task_message = request_json.get('message')
    task_repeat = request_json.get('repeat', 0)
    task_delta = request_json.get('timedelta', 0)

    if not task_id:
        logging.error('Received cloud task without ID')
        return

    logging.info({
        "message": "Task execution started",
        "data": request_json
    })

    # create next task if repeat is set
    finished_processing = False
    if task_repeat and task_repeat > 1:
        next_task = CalendarTask(
            id=task_id,
            timedelta=task_delta,
            repeat=task_repeat - 1,
            message=task_message
        )
        client.create_task(
            parent=task_queue,
            task=next_task.to_task_request()
        )
    else:
        finished_processing = True

    # increment repeated counter
    transaction = db.transaction()
    increment_execution_counter(
        transaction,
        db.collection('events').document(task_id),
        finished_processing
    )

    # send slack message
    if slack_client and 'message' in request_json:
        slack_client.chat_postMessage(
            channel=slack_channel,
            text=":exclamation: {message} :exclamation: (ID: {id}){repetition}".format(
                message=task_message,
                id=task_id,
                repetition=' [repetitions left: {}]'.format(task_repeat) if task_repeat else ''
            )
        )


@transactional
def increment_execution_counter(
        transaction: Transaction,
        event_reference: DocumentReference,
        finished_processing: bool
):
    """Increments execution counter in a task

    :param transaction: transaction
    :param event_reference: event document reference
    :param finished_processing: flags whether the repeated task processing has been finished
    """
    event = event_reference.get().to_dict()
    transaction.update(event_reference, {
        'execution_counter': event.get('execution_counter', 0) + 1,
        'processed': finished_processing,
    })
