import datetime
import logging
import os
import uuid

import google.auth
import requests
from flask import Request
from google.auth.transport.requests import AuthorizedSession
from google.cloud import logging as cloud_logging
from slack import WebClient

# set up logging for nice logs
log_client = cloud_logging.Client()
log_handler = log_client.get_default_handler()
cloud_logger = logging.getLogger("cloudLogger")
cloud_logger.setLevel(logging.INFO)
cloud_logger.addHandler(log_handler)

# prepare slack client
slack_api_token = os.getenv('SLACK_API_TOKEN')
slack_channel = os.getenv("SLACK_CHANNEL")
if not (slack_api_token and slack_channel):
    slack_client = None
else:
    slack_client = WebClient(token=slack_api_token)

# get credentials from the environment
credentials, project = google.auth.default(
    scopes=[
        'https://www.googleapis.com/auth/datastore',
        'https://www.googleapis.com/auth/cloud-platform'
    ]
)


def backup_firestore(request: Request):
    """Backs up firestore DB

    :param request: flask Request
    """
    bucket_name = os.getenv('BACKUP_BUCKET')
    if not bucket_name:
        logging.error({
            "message": "Failed to perform backup",
            "reason": "Unspecified bucket"
        })

    prefix = "{timestamp}U{id}".format(
        timestamp=datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        id=str(uuid.uuid4())[:8]
    )

    # create backup
    authorized_session = AuthorizedSession(credentials)
    response: requests.Response = authorized_session.post(
        'https://firestore.googleapis.com/v1beta1/projects/{project}/databases/(default):exportDocuments'.format(
            project=os.getenv('GCP_PROJECT')
        ),
        json={
            "outputUriPrefix": "gs://{prefix}/{bucket}".format(prefix=prefix, bucket=bucket_name)
        }
    )
    logging.info({
        "message": "Firestore backup process finished",
        "result": "success" if response.status_code == 200 else "failure",
        "payload": response.text
    })

    if slack_client:
        if response.status_code == 200:
            slack_client.chat_postMessage(
                channel=slack_channel,
                text="Firestore DB for *{project}* has been backed up. :partyparrot:".format(
                    project=os.getenv('GCP_PROJECT')
                )
            )
        else:
            slack_client.chat_postMessage(
                channel=slack_channel,
                text="Backup of Firestore DB for *{project}* has failed. :sadparrot:".format(
                    project=os.getenv('GCP_PROJECT')
                )
            )
