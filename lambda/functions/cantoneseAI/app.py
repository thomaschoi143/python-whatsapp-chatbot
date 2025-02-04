import requests
import json
import logging
from shared_utils import get_secret

logger = logging.getLogger()
logger.setLevel(logging.INFO)

API_KEY = get_secret("prod/cantoneseAI")["API_KEY"]
VOICE_ID = get_secret("prod/cantoneseAI")["VOICE_ID"]

url = "https://cantonese.ai/api/tts"


def lambda_handler(event, context):
    text = event["text"]

    payload = json.dumps(
        {
            "api_key": API_KEY,
            "text": text,
            "speed": 0.85,
            "pitch": 1,
            "output_extension": "mp3",
            "voice_id": VOICE_ID,
            "should_enhance": False,
        }
    )
    headers = {"Content-Type": "application/json"}

    response = requests.request("POST", url, headers=headers, data=payload, stream=True)
    if response.status_code == 200:
        logging.info(f"Cantonese AI: successful, {text}")
        return {"audio": response.raw}

    logging.info(f"Cantonese AI Error: {response.status_code} {response.text}, {text}")
    return {"audio": None}
