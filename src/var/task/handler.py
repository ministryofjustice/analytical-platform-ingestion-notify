import boto3
import botocore.exceptions
from notifications_python_client.notifications import NotificationsAPIClient

notifications_client = NotificationsAPIClient("API_KEY")
NOTIFICATIONS_TEMPLATE_ID = ""
NOTIFICATION_EMAIL_ADDRESS = ""

sm_client = boto3.client("secretsmanager")


def handler(event, context):
    print("Received event:", event)
    print("Received context:", context)
    message = event["Records"][0]["Sns"]["Message"]
    state, object_key, time_stamp = message.split(",")[:3]
    print(f"State: {state}")
    print(f"Object key: {object_key}")
    print(f"Time stamp: {time_stamp}")

    if state == "infected":
        print("Infected file detected")
    elif state == "synced":
        print("File synced")

    try:
        supplier, file_name = object_key.split("/")[:2]
        print(f"Supplier: {supplier}")
        print(f"File name: {file_name}")

        notifications_client.send_email_notification(
            template_id=NOTIFICATIONS_TEMPLATE_ID,
            email_address=NOTIFICATION_EMAIL_ADDRESS,
            personalisation={"username": supplier, "filename": file_name},
        )
    except Exception as e:
        print(f"Error: {e}")
        raise e

    try:
        notifications_client.send_email_notification(
            template_id=NOTIFICATIONS_TEMPLATE_ID,
            email_address=NOTIFICATION_EMAIL_ADDRESS,
            personalisation={"username": supplier, "filename": file_name},
        )
    except Exception as e:
        print(f"Error: {e}")
        raise e
