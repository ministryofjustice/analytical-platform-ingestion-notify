import json
import os

import boto3
from notifications_python_client.notifications import NotificationsAPIClient
from slack_sdk import WebClient

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
slack_token_secret = os.environ["SLACK_TOKEN_SECRET"]
slack_token = sm_client.get_secret_value(SecretId=slack_token_secret)["SecretString"]
slack_client = WebClient(token=slack_token)


def supplier_configuration(supplier):
    data_contact = sm_client.get_secret_value(
        SecretId=f"ingestion/sftp/{supplier}/data-contact"
    )["SecretString"]

    technical_contact = sm_client.get_secret_value(
        SecretId=f"ingestion/sftp/{supplier}/technical-contact"
    )["SecretString"]

    slack_channel = sm_client.get_secret_value(
        SecretId=f"ingestion/sftp/{supplier}/slack-channel"
    )["SecretString"]

    target_bucket = sm_client.get_secret_value(
        SecretId=f"ingestion/sftp/{supplier}/target-bucket"
    )["SecretString"]

    return data_contact, technical_contact, slack_channel, target_bucket


def send_slack(slack_channel, message):
    response = slack_client.chat_postMessage(
        channel=slack_channel,
        text=message,
    )
    return response


def send_gov_uk_notify(template, email_address, personalisation):
    response = notifications_client.send_email_notification(
        template_id=template,
        email_address=email_address,
        personalisation=personalisation,
    )
    return response


def handler(event, context):  # pylint: disable=unused-argument
    print("Received event:", event)
    print("Received context:", context)
    try:
        mode = os.environ.get("MODE")
        if mode == "quarantined":
            # This mode expects S3 bucket notifications via SNS
            object_key = event["Records"][0]["s3"]["object"]["key"]
            supplier, file_name = object_key.split("/")[:2]
            supplier_config = supplier_configuration(supplier=supplier)

            # GOV.UK Notify Data Contact
            send_gov_uk_notify(
                template=govuk_notify_templates["sftp_quarantined_file_data_contact"],
                email_address=supplier_config[0],
                personalisation={"filename": file_name},
            )

            # GOV.UK Notify Technical Contact
            send_gov_uk_notify(
                template=govuk_notify_templates[
                    "sftp_quarantined_file_technical_contact"
                ],
                email_address=supplier_config[1],
                personalisation={
                    "filename": file_name,
                    "supplier": supplier,
                },
            )

            # Slack Technical Contact
            if supplier_config[2]:
                send_slack(
                    slack_channel=supplier_config[2],
                    message=f"File {file_name} from {supplier} has been quarantined.",
                )
            else:
                print(f"No Slack channel configured for {supplier}")

        elif mode == "transferred":
            # This mode expects CSV style notifications from
            # the transfer Lambda
            # e.g, "transferred,{supplier}/{file_name},{timestamp}"
            message = event["Records"][0]["Sns"]["Message"]
            state, object_key, timestamp = message.split(  # pylint: disable=unused-variable
                ","
            )
            supplier, file_name = object_key.split("/")[:2]
            supplier_config = supplier_configuration(supplier=supplier)

            # GOV.UK Notify Technical Contact
            send_gov_uk_notify(
                template=govuk_notify_templates[
                    "sftp_transferred_file_technical_contact"
                ],
                email_address=supplier_config[1],
                personalisation={
                    "filename": file_name,
                    "supplier": supplier,
                    "targetlocation": supplier_config[3],
                },
            )

            # Slack Technical Contact
            if supplier_config[2]:
                send_slack(
                    slack_channel=supplier_config[2],
                    message=f"A file uploaded by `{supplier}` has been transferred to `{supplier_config[3]}`.\n  • `{file_name}`",
                )
            else:
                print(f"No Slack channel configured for {supplier}")

        else:
            raise ValueError(f"Invalid mode: {mode}")

        return {"statusCode": 200, "body": json.dumps({"message": "Success"})}
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return {"statusCode": 400, "body": json.dumps({"message": str(e)})}
