from shared_utils import update_dynamodb_item

users_table_name = "chatbot-users"


def lambda_handler(event, context):
    wa_id, audio_enabled = event["wa_id"], event["audio_enabled"]
    new_audio_enabled = not audio_enabled

    update = update_dynamodb_item(users_table_name, "wa_id", wa_id, "audio_enabled", new_audio_enabled)
    if update:
        response = f'You have successfully {"enabled" if new_audio_enabled else "disabled"} audio responses'
    else:
        response = "Sorry, the update has failed."

    return {"response": response}
