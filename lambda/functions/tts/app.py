import requests
import boto3
from shared_utils import get_secret

SECRETS = get_secret("prod/wtsChatbot")
ACCESS_TOKEN = SECRETS["ACCESS_TOKEN"]
VERSION = SECRETS["VERSION"]
PHONE_NUMBER_ID = SECRETS["PHONE_NUMBER_ID"]

polly = boto3.client("polly")


def lambda_handler(event, context):
    text = event["text"]

    response = polly.synthesize_speech(
        Text=text,
        OutputFormat="mp3",  # Choose output format: "mp3", "ogg_vorbis", "pcm"
        VoiceId="Joanna",  # Select a voice
    )

    audio_stream = response["AudioStream"].read()

    files = {"file": ("audio.mp3", audio_stream, "audio/mpeg")}
    data = {"messaging_product": "whatsapp"}
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    # Send POST request
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/media"
    response = requests.post(url, files=files, data=data, headers=headers)

    return {"media_id": response.json()["id"]}
