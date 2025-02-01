import boto3

dynamodb = boto3.resource("dynamodb")
stickers_table = dynamodb.Table("chatbot-stickers")


def get_all_stickers_description():
    response = stickers_table.scan(ProjectionExpression="description")
    descriptions = [item["description"] for item in response.get("Items", []) if "description" in item]

    return descriptions


def get_sticker_s3_url(name):
    filename = f"{name}.webp"
    response = stickers_table.get_item(Key={"filename": filename}, ProjectionExpression="s3_url")  # Fetch only s3_url

    return response.get("Item", {}).get("s3_url")
