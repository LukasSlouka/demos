import json
import logging
import os

from firebase_admin import (
    firestore,
    initialize_app,
)
from flask import Request
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

    request_json = json.loads(request.data)
    task_id = request_json.get('id')
    if not task_id:
        logging.error('Received cloud task without ID')
        return

    logging.info({
        "message": "Task execution started",
        "id": request_json.get('id'),
        "data": request_json
    })

    db.collection('events').document(task_id).update({
        'processed': True
    })

    if slack_client and 'message' in request_json:
        slack_client.chat_postMessage(
            channel=slack_channel,
            text=":exclamation: {} :exclamation: (ID: {})".format(request_json['message'], task_id)
        )
