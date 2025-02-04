import json
import requests
import logging
from shared_utils import get_secret

logger = logging.getLogger()
logger.setLevel(logging.INFO)

WTS_KEYS = get_secret("prod/wtsChatbot")


def get_response_message_input(recipient, type, response):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": type,
            type: {"id" if type == "audio" else "link": response} if type != "text" else None,
            "text": {"preview_url": False, "body": response} if type == "text" else None,
        }
    )


def lambda_handler(event, context):
    recipient, type, response = event["recipient"], event["type"], event["response"]
    data = get_response_message_input(recipient, type, response)
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {WTS_KEYS['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{WTS_KEYS['VERSION']}/{WTS_KEYS['PHONE_NUMBER_ID']}/messages"

    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return {"statusCode": 408, "body": json.dumps({"message": "Request timed out"})}
    except requests.RequestException as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return {"statusCode": 500, "body": json.dumps({"message": "Failed to send message"})}
    else:
        # Process the response as normal
        logging.info(f"Sent message to {recipient}, type: {type}")
        return {"statusCode": response.status_code, "body": response.json()}
