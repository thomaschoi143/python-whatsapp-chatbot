import requests
import json
from dotenv import load_dotenv, find_dotenv
import os
import logging
from pydub import AudioSegment
import sys


def trim_mp3(input_file, output_file, trim_ms=800):
    """
    Trims the first `trim_ms` milliseconds from an MP3 file.
    :param input_file: Path to the input MP3 file.
    :param output_file: Path to save the trimmed MP3 file.
    :param trim_ms: Number of milliseconds to trim from the beginning (default: 1000ms = 1s).
    """
    try:
        # Load the MP3 file
        audio = AudioSegment.from_mp3(input_file)

        # Trim the first `trim_ms` milliseconds
        trimmed_audio = audio[trim_ms:]

        # Export the trimmed audio to a new MP3 file
        trimmed_audio.export(output_file, format="mp3")
        logging.info(f"Trimmed audio saved")
    except Exception as e:
        logging.info(f"Error processing file: {e}")


load_dotenv(find_dotenv())
CANTONESE_AI_API_KEY = os.getenv("CANTONESE_AI_API_KEY")
VOICE_ID = os.getenv("VOICE_ID")


def get_cantonese_audio(text):
    url = "https://cantonese.ai/api/tts"

    payload = json.dumps(
        {
            "api_key": CANTONESE_AI_API_KEY,
            "text": text,
            "tts_mode": "tts_with_voice_cloning",
            "tts_model_version": "v2",
            "speed": 0.85,
            "pitch": 1,
            "output_extension": "mp3",
            "voice_clone_voice_id": VOICE_ID,
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
