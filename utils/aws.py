import boto3
import os
from pathlib import Path

# Initialize S3 and DynamoDB clients
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

# Define your S3 bucket and DynamoDB table
bucket_name = "thomas-chatbot"
stickers_table = dynamodb.Table("chatbot-stickers")

script_dir = Path(__file__).parent


# Function to upload sticker to S3 and insert metadata into DynamoDB
def upload_sticker_and_metadata(file_path, description):

    # Get the filename
    filename = os.path.basename(file_path)

    response = stickers_table.get_item(Key={"filename": filename})
    if "Item" in response:
        print(f"Sticker {filename} already exists. Skipping insert.")
        return

    # Define the S3 key (path in the bucket)
    s3_key = f"stickers/{filename}"

    # Upload the file to S3
    s3.upload_file(file_path, bucket_name, s3_key, ExtraArgs={"ContentType": "image/webp"})

    # Get the URL of the uploaded file
    s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"

    # Insert metadata into DynamoDB
    response = stickers_table.put_item(Item={"filename": filename, "description": description, "s3_url": s3_url})

    print(f"Sticker uploaded and metadata added for: {filename}")


def clear_dynamodb_table(table, pk_name):
    scan = table.scan(ProjectionExpression="#k", ExpressionAttributeNames={"#k": pk_name})
    with table.batch_writer() as batch:
        for item in scan["Items"]:
            batch.delete_item(Key={pk_name: item[pk_name]})
    print(f"Deleted {len(scan['Items'])} items from {table.table_name} table")


def clear_s3_folder(bucket, prefix):
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    if "Contents" in response:
        objects_to_delete = [{"Key": obj["Key"]} for obj in response["Contents"]]
        s3.delete_objects(Bucket=bucket, Delete={"Objects": objects_to_delete})
        print(f"Deleted {len(objects_to_delete)} files from {prefix} folder")


# Function to process all stickers in the folder
def upload_stickers_from_folder(folder_path):
    clear_dynamodb_table(stickers_table, "filename")
    clear_s3_folder("thomas-chatbot", "stickers")

    # Iterate through all files in the folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Ensure it's a file (not a directory)
        if os.path.isfile(file_path) and filename.endswith(".webp"):
            # You can modify this description as needed
            description = os.path.splitext(filename)[0]

            # Upload the sticker and insert metadata into DynamoDB
            upload_sticker_and_metadata(file_path, description)


folder = Path("../data/stickers")
upload_stickers_from_folder(script_dir / folder)
