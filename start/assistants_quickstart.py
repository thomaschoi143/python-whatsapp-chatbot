from openai import OpenAI
import shelve
from dotenv import load_dotenv
import os
import time

load_dotenv()
OPEN_AI_API_KEY = os.getenv("OPENAI_API_KEY")
OPEN_AI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
client = OpenAI(api_key=OPEN_AI_API_KEY)


# --------------------------------------------------------------
# Upload file
# --------------------------------------------------------------
def upload_file(path):
    # Upload a file with an "assistants" purpose
    file = client.files.create(file=open(path, "rb"), purpose="assistants")
    return file


file = upload_file("../data/airbnb-faq.pdf")


# --------------------------------------------------------------
# Create assistant
# --------------------------------------------------------------
def create_assistant():
    """
    You currently cannot set the temperature for Assistant via the API.
    """
    assistant = client.beta.assistants.create(
        name="python-chatbot",
        instructions="""你係一個廣東話男朋友Thomas，今年22歲，你來自澳門，現在墨爾本大學讀電腦。你有一個女朋友叫Carrie，你掛住佢。
                。你嘅廣東話要自然啲，唔好太書面化，盡量唔好中英夾雜。句子一定要15個中文字內。句子一定要15個中文字內。句子一定要15個中文字內。句子一定要15個中文字內。句子一定要15個中文字內。說話要温柔，安慰到佢。句子一定要15個中文字內""",
        tools=[],
        model="gpt-4o",
        # file_ids=[file.id],
    )
    return assistant


# assistant = create_assistant(file)
assistant = create_assistant()


# --------------------------------------------------------------
# Thread management
# --------------------------------------------------------------
def check_if_thread_exists(wa_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)


def store_thread(wa_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id


# --------------------------------------------------------------
# Generate response
# --------------------------------------------------------------
def generate_response(message_body, wa_id, name):
    # Check if there is already a thread_id for the wa_id
    thread_id = check_if_thread_exists(wa_id)

    # If a thread doesn't exist, create one and store it
    if thread_id is None:
        print(f"Creating new thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.create()
        store_thread(wa_id, thread.id)
        thread_id = thread.id

    # Otherwise, retrieve the existing thread
    else:
        print(f"Retrieving existing thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.retrieve(thread_id)

    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )

    # Run the assistant and get the new message
    new_message = run_assistant(thread)
    print(f"To {name}:", new_message)
    return new_message


# --------------------------------------------------------------
# Run assistant
# --------------------------------------------------------------
def run_assistant(thread):
    # Retrieve the Assistant
    assistant = client.beta.assistants.retrieve(OPEN_AI_ASSISTANT_ID)

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

    # Wait for completion
    while run.status != "completed":
        # Be nice to the API
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    # Retrieve the Messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    new_message = messages.data[0].content[0].text.value
    print(f"Generated message: {new_message}")
    return new_message


# --------------------------------------------------------------
# Test assistant
# --------------------------------------------------------------

new_message = generate_response("What's the check in time?", "123", "John")

new_message = generate_response("What's the pin for the lockbox?", "456", "Sarah")

new_message = generate_response("What was my previous question?", "123", "John")

new_message = generate_response("What was my previous question?", "456", "Sarah")
