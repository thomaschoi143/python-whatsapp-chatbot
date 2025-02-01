from dotenv import load_dotenv
import os
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.services.aws_service import get_all_stickers_description
from langchain_core.runnables.history import RunnableWithMessageHistory
import re
from langchain_community.chat_message_histories import DynamoDBChatMessageHistory

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
GF_WA_ID = os.getenv("GF_WA_ID")
MY_WA_ID = os.getenv("MY_WA_ID")
FM_WA_IDS = os.getenv("FM_WA_IDS", "").split(",")

# client = OpenAI(api_key=OPENAI_API_KEY)
model = ChatOpenAI(model="gpt-4o")
logging.info("LLM client started")

stickers_description = get_all_stickers_description()
# def upload_file(path):
#     # Upload a file with an "assistants" purpose
#     file = client.files.create(file=open("../../data/airbnb-faq.pdf", "rb"), purpose="assistants")


# def create_assistant(file):
#     """
#     You currently cannot set the temperature for Assistant via the API.
#     """
#     assistant = client.beta.assistants.create(
#         name="WhatsApp AirBnb Assistant",
#         instructions="You're a helpful WhatsApp assistant that can assist guests that are staying in our Paris AirBnb. Use your knowledge base to best respond to customer queries. If you don't know the answer, say simply that you cannot help with question and advice to contact the host directly. Be friendly and funny.",
#         tools=[{"type": "retrieval"}],
#         model="gpt-3.5-turbo",
#         file_ids=[file.id],
#     )
#     return assistant


# Use context manager to ensure the shelf file is closed properly
# def check_if_thread_exists(wa_id):
#     with shelve.open("threads_db") as threads_shelf:
#         return threads_shelf.get(wa_id, None)


# def store_thread(wa_id, thread_id):
#     with shelve.open("threads_db", writeback=True) as threads_shelf:
#         threads_shelf[wa_id] = thread_id


# def run_assistant(thread, name):
#     # Retrieve the Assistant
#     assistant = client.beta.assistants.retrieve(OPENAI_ASSISTANT_ID)

#     # Run the assistant
#     run = client.beta.threads.runs.create(
#         thread_id=thread.id,
#         assistant_id=assistant.id,
#         # instructions=f"You are having a conversation with {name}",
#     )

#     # Wait for completion
#     # https://platform.openai.com/docs/assistants/how-it-works/runs-and-run-steps#:~:text=under%20failed_at.-,Polling%20for%20updates,-In%20order%20to
#     while run.status != "completed":
#         # Be nice to the API
#         time.sleep(0.5)
#         run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

#     # Retrieve the Messages
#     messages = client.beta.threads.messages.list(thread_id=thread.id)
#     new_message = messages.data[0].content[0].text.value
#     logging.info(f"Generated message: {new_message}")
#     return new_message


# def generate_response(message_body, wa_id, name):
#     # Check if there is already a thread_id for the wa_id
#     thread_id = check_if_thread_exists(wa_id)

#     # If a thread doesn't exist, create one and store it
#     if thread_id is None:
#         logging.info(f"Creating new thread for {name} with wa_id {wa_id}")
#         thread = client.beta.threads.create()
#         store_thread(wa_id, thread.id)
#         thread_id = thread.id

#     # Otherwise, retrieve the existing thread
#     else:
#         logging.info(f"Retrieving existing thread for {name} with wa_id {wa_id}")
#         thread = client.beta.threads.retrieve(thread_id)

#     # Add message to thread
#     message = client.beta.threads.messages.create(
#         thread_id=thread_id,
#         role="user",
#         content=message_body,
#     )

#     # Run the assistant and get the new message
#     new_message = run_assistant(thread, name)

#     return new_message


def decide_system_msg(wa_id, name):
    system_msg = f"You are a helpful WhatsApp assistant. You are serving {name}"
    sticker_instruction = f"回覆中在這裏選擇合適的情緒：{stickers_description}。"
    if wa_id == GF_WA_ID:
        system_msg = """你係一個廣東話男朋友Thomas，今年22歲，你來自澳門，現在墨爾本大學讀電腦。你有一個女朋友叫Carrie，你掛住佢。
                    。你嘅廣東話要自然啲，唔好太書面化，盡量唔好中英夾雜。句子一定要30個中文字內。說話要温柔，安慰到佢，陪人傾計。句子一定要30個中文字內。"""
        system_msg += sticker_instruction
    elif wa_id == MY_WA_ID:
        system_msg = """你係一個繁體中文廣東話助手。廣東話要自然啲。廣東話要自然啲。句子一定要30個中文字內。句子一定要30個中文字內。你服務緊Thomas。"""
        system_msg += sticker_instruction
    elif wa_id in FM_WA_IDS:
        system_msg = f"你係一個廣東話助手Thomas。你有屋企人叫{name}。熱心助人。幫助解決屋企大小事。"
    return system_msg


def generate_response(message_body, wa_id, name):

    system_msg = decide_system_msg(wa_id, name)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_msg),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{human_input}"),
        ]
    )

    chain = prompt | model
    chat_history_table = "chatbot-history"
    chain_with_history = RunnableWithMessageHistory(
        chain,
        lambda session_id: DynamoDBChatMessageHistory(
            table_name=chat_history_table, session_id=session_id, primary_key_name="session_id"
        ),
        input_messages_key="human_input",
        history_messages_key="history",
    )

    config = {"configurable": {"session_id": wa_id}}

    result = chain_with_history.invoke({"human_input": message_body}, config=config)

    matching = re.match(r"(.*)\*(.*)\*", result.content)

    response = matching.group(1).strip()
    sticker_name = matching.group(2)

    logging.info(f"Generated message: [{response}] [{sticker_name}]")

    return response, sticker_name
