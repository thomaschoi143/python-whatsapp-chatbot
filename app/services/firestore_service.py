from dotenv import load_dotenv, find_dotenv
from langchain_google_firestore import FirestoreChatMessageHistory
from google.cloud import firestore
import os
import logging

load_dotenv(find_dotenv())
FIRESTORE_PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID")
FIRESTORE_COLLECTION_NAME = os.getenv("FIRESTORE_COLLECTION_NAME")

firestore_client = firestore.Client(project=FIRESTORE_PROJECT_ID)
logging.info("Firestore client started")


def get_chat_history(wa_id):
    chat_history = FirestoreChatMessageHistory(
        session_id=wa_id,
        collection=FIRESTORE_COLLECTION_NAME,
        client=firestore_client,
    )
    return chat_history
