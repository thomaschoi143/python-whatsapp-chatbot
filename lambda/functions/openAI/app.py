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
PHONE_KEYS = get_secret("prod/phone")
GF_WA_ID = PHONE_KEYS["GF_WA_ID"]
MY_WA_ID = PHONE_KEYS["MY_WA_ID"]
FM_WA_IDS = PHONE_KEYS["FM_WA_IDS"].split(",")

model = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)
stickers_description = db_get_all_variables("chatbot-stickers", "description")


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


def lambda_handler(event, context):
    if event.get("warmer", False):
        logging.info("Warmed up")
        return {"status": "warmed up"}

    message_body, wa_id, name = event["text"], event["wa_id"], event["name"]
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

    return {"response": response, "sticker": sticker_name}
