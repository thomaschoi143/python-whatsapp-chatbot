import boto3
import os
import uuid
from boto3.dynamodb.conditions import Key

# Initialize S3 and DynamoDB clients
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

# Define your S3 bucket and DynamoDB table
bucket_name = "thomas-chatbot"
dynamo_table = dynamodb.Table("chatbot-stickers")


# Function to upload sticker to S3 and insert metadata into DynamoDB
def upload_sticker_and_metadata(file_path, description):
    # Generate unique sticker ID (UUID)
    sticker_id = str(uuid.uuid4())

    # Get the filename
    filename = os.path.basename(file_path)

    # Define the S3 key (path in the bucket)
    s3_key = f"stickers/{sticker_id}_{filename}"

    # Upload the file to S3
    s3.upload_file(file_path, bucket_name, s3_key)

    # Get the URL of the uploaded file
    s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"

    # Insert metadata into DynamoDB
    response = dynamo_table.put_item(
        Item={"id": sticker_id, "description": description, "filename": filename, "s3_url": s3_url}
    )

    print(f"Sticker uploaded and metadata added for: {filename}")
    return response


# Function to process all stickers in the folder
def upload_stickers_from_folder(folder_path):
    # Iterate through all files in the folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Ensure it's a file (not a directory)
        if os.path.isfile(file_path) and filename.endswith(".webp"):
            # You can modify this description as needed
            description = os.path.splitext(filename)[0]

            # Upload the sticker and insert metadata into DynamoDB
            upload_sticker_and_metadata(file_path, description)


# Example usage:
folder_path = "../data/stickers"  # Change this to your folder path
upload_stickers_from_folder(folder_path)
