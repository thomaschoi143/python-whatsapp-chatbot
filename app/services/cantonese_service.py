import requests
import json
from dotenv import load_dotenv, find_dotenv
import os
import logging


load_dotenv(find_dotenv())
CANTONESE_AI_API_KEY = os.getenv("CANTONESE_AI_API_KEY")
VOICE_ID = os.getenv("VOICE_ID")


def get_cantonese_audio(text):
    url = "https://cantonese.ai/api/tts"

    payload = json.dumps(
        {
            "api_key": CANTONESE_AI_API_KEY,
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
        # trim_mp3(audio_filename, audio_filename)
        logging.info("Cantonese AI: successful")
        return response.raw

    logging.info(f"Cantonese AI Error: {response.status_code}")
    logging.info(f"Cantonese AI Text: {response.text}")
    return None
