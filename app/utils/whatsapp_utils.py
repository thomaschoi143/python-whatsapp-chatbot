import logging
from flask import current_app, jsonify
import json
import requests

from app.services.openai_service import generate_response
from app.services.cantonese_service import get_cantonese_audio
import re
import os


def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    # logging.info(f"Content-type: {response.headers.get('content-type')}")
    # logging.info(f"Body: {response.text}")


def get_response_message_input(recipient, type, response):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": type,
            type: {"id": response} if type != "text" else None,
            "text": {"preview_url": False, "body": response} if type == "text" else None,
        }
    )


# def generate_response(response):
#     # Return text in uppercase
#     return response.upper()


def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except requests.RequestException as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        log_http_response(response)
        return response


# def process_text_for_whatsapp(text):
#     # Remove brackets
#     pattern = r"\【.*?\】"
#     # Substitute the pattern with an empty string
#     text = re.sub(pattern, "", text).strip()

#     # Pattern to find double asterisks including the word(s) in between
#     pattern = r"\*\*(.*?)\*\*"

#     # Replacement pattern with single asterisks
#     replacement = r"*\1*"

#     # Substitute occurrences of the pattern with the replacement
#     whatsapp_style_text = re.sub(pattern, replacement, text)

#     return whatsapp_style_text


def upload_media(media, filename):
    with open(filename, "rb") as audio_file:
        files = {"file": (filename, audio_file, media)}
        data = {"messaging_product": "whatsapp"}  # Specify that it's an audio file
        headers = {"Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}"}

        # Send POST request
        url = (
            f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/media"
        )
        response = requests.post(url, files=files, data=data, headers=headers)

    return response.json()["id"]


def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]

    if "sticker" in message:
        sticker_id = "589740883852670"
        logging.info(f"Received message from {wa_id} {name}: sticker")
        logging.info(f"Respond with sticker: smile")
        data = get_response_message_input(wa_id, "sticker", sticker_id)
        send_message(data)

    elif "text" in message:
        message_body = message["text"]["body"]
        logging.info(f"Received message from {wa_id} {name}: {message_body}")

        # OpenAI Integration
        response = generate_response(message_body, wa_id, name)
        # response = process_text_for_whatsapp(response)

        # data = get_response_message_input(wa_id, "text", response)
        # send_message(data)

        # Cantonese AI Integration
        audio_filename = get_cantonese_audio(response)

        if not audio_filename:
            data = get_response_message_input(wa_id, "text", "唔好意思 我唔明白")
            send_message(data)
            return

        audio_id = upload_media("audio/mpeg", audio_filename)
        data = get_response_message_input(wa_id, "audio", audio_id)
        send_message(data)
    else:
        data = get_response_message_input(wa_id, "text", "唔好意思 我而家淨係可以收text message同sticker")
        send_message(data)
        return


def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )
