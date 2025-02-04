import logging
from shared_utils import get_secret

logger = logging.getLogger()
logger.setLevel(logging.INFO)

WTS_KEYS = get_secret("prod/wtsChatbot")


def lambda_handler(event, context):
    # Parse params from the webhook verification request
    mode = event.get("queryStringParameters", {}).get("hub.mode", None)
    token = event.get("queryStringParameters", {}).get("hub.verify_token", None)
    challenge = event.get("queryStringParameters", {}).get("hub.challenge", None)

    # Check if a token and mode were sent
    if mode and token:
        # Check the mode and token sent are correct
        if mode == "subscribe" and token == WTS_KEYS["VERIFY_TOKEN"]:
            # Respond with 200 OK and challenge token from the request
            logging.info("WEBHOOK_VERIFIED")
            return {"statusCode": 200, "body": challenge}
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            logging.info("VERIFICATION_FAILED")
            return {"statusCode": 403, "body": "Verification failed"}
    else:
        # Responds with '400 Bad Request' if verify tokens do not match
        logging.info("MISSING_PARAMETER")
        return {"statusCode": 400, "body": "Missing parameters"}
