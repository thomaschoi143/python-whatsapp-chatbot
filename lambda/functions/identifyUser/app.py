from shared_utils import db_get_variable_by_key, db_get_all_variables, db_get_variables_by_key, db_add_item

stickers_description = db_get_all_variables("chatbot-stickers", "description")
users_table_name = "chatbot-users"


def lambda_handler(event, context):
    wa_id, name = event["wa_id"], event["name"]
    user = db_get_variables_by_key(users_table_name, "wa_id", wa_id, ["user_role", "audio_enabled"])
    if not user:
        db_add_item(users_table_name, {"wa_id": wa_id, "user_role": "PUBLIC", "audio_enabled": True})
        user_role, audio_enabled = "PUBLIC", True
    else:
        user_role, audio_enabled = user["user_role"], user["audio_enabled"]

    system_msg = f"You are a helpful assistant on WhatsApp. You are serving {name}."
    sticker_instruction = f"記住回覆中在這裏選擇合適的情緒：{stickers_description}。（以*分隔，放在回覆後）。"
    if user_role == "GF":
        system_msg = """你係一個廣東話男朋友Thomas，今年22歲，你來自澳門，現在墨爾本大學讀電腦。你有一個女朋友叫Carrie，你掛住佢。
                    。你嘅廣東話要自然啲，唔好太書面化，盡量唔好中英夾雜。句子一定要30個中文字內。說話要温柔，安慰到佢，陪人傾計。句子一定要30個中文字內。"""
        system_msg += sticker_instruction
    elif user_role == "ME":
        system_msg = """你係一個繁體中文廣東話助手。廣東話要自然啲。廣東話要自然啲。句子一定要30個中文字內。句子一定要30個中文字內。你服務緊Thomas。"""
        system_msg += sticker_instruction
    elif user_role == "FAMILY":
        system_msg = f"你係一個廣東話助手Thomas。你有屋企人叫{name}。熱心助人。幫助解決屋企大小事。"
    return {"system_msg": system_msg, "audio_enabled": audio_enabled}


# print(lambda_handler({"wa_id": "61468951809", "name": "Thomas"}, None))
