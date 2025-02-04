from shared_utils import db_get_variable_by_key


def lambda_handler(event, context):
    sticker = event["sticker"]
    url = db_get_variable_by_key("chatbot-stickers", "filename", f"{sticker}.webp", "s3_url")
    return {"sticker_url": url}
