import json
import os

import boto3
from notifications_python_client.notifications import NotificationsAPIClient

sm_client = boto3.client("secretsmanager")
govuk_notify_api_key_secret = os.environ["GOVUK_NOTIFY_API_KEY_SECRET"]
govuk_notify_api_key = sm_client.get_secret_value(SecretId=govuk_notify_api_key_secret)[
    "SecretString"
]
govuk_notify_templates_secret = os.environ["GOVUK_NOTIFY_TEMPLATES_SECRET"]
govuk_notify_templates = json.loads(
    sm_client.get_secret_value(SecretId=govuk_notify_templates_secret)["SecretString"]
)
notifications_client = NotificationsAPIClient(govuk_notify_api_key)


def handler(event, context):
    print("Received event:", event)
    print("Received context:", context)

    s3_bucket = event["Records"][0]["s3"]["bucket"]["name"]
    object_key = event["Records"][0]["s3"]["object"]["key"]

    supplier, file_name = object_key.split("/")[:2]
    print(f"Supplier: {supplier}")
    print(f"File name: {file_name}")

    supplier_data_contact = sm_client.get_secret_value(
        SecretId=f"ingestion/sftp/{supplier}/data-contact"
    )["SecretString"]
    # supplier_data_owner = sm_client.get_secret_value(
    #     SecretId=f"ingestion/sftp/{supplier}/technical-contact"
    # )["SecretString"]

    if s3_bucket == "analytical-platform-quarantine":
        print("File quarantined")
        # send data owner
        # notifications_client.send_email_notification(
        #     template_id=govuk_notify_templates["sftp_quarantined_file_data_owner"],
        #     email_address=supplier_data_owner,
        #     personalisation={"supplier": supplier, "filename": file_name},
        # )
        # send data contact
        notifications_client.send_email_notification(
            template_id=govuk_notify_templates["sftp_quarantined_file_supplier"],
            email_address=supplier_data_contact,
            personalisation={"filename": file_name},
        )
    else:
        print(s3_bucket)
