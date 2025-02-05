import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
import re
from langchain_community.chat_message_histories import DynamoDBChatMessageHistory
from shared_utils import get_secret, db_get_all_variables

logger = logging.getLogger()
logger.setLevel(logging.INFO)

OPENAI_API_KEY = get_secret("prod/openAI")["API_KEY"]

model = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)


def lambda_handler(event, context):
    if event.get("warmer", False):
        logging.info("Warmed up")
        return {"status": "warmed up"}

    message_body, wa_id, system_msg = event["text"], event["wa_id"], event["system_msg"]

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
            table_name=chat_history_table, session_id=session_id, primary_key_name="session_id", history_size=20
        ),
        input_messages_key="human_input",
        history_messages_key="history",
    )

    config = {"configurable": {"session_id": wa_id}}

    response = chain_with_history.invoke({"human_input": message_body}, config=config).content
    sticker_name = None

    matching = re.match(r"(.*)\*(.*)\*", response)
    if matching:
        response = matching.group(1).strip()
        sticker_name = matching.group(2)

    logging.info(f"Generated message: [{response}] [{sticker_name}]")

    return {"response": response, "sticker": sticker_name}
