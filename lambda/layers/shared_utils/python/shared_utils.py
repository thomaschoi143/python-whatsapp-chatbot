import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_secret(secret_name):
    """
    Retrieves a secret from AWS Secrets Manager.
    """
    client = boto3.client("secretsmanager")

    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response["SecretString"])
    return secret


dynamodb = boto3.resource("dynamodb")


def db_get_all_variables(table_name, variable):
    table = dynamodb.Table(table_name)
    response = table.scan(ProjectionExpression=variable)
    variables = [item[variable] for item in response.get("Items", []) if variable in item]

    return variables


def db_get_variable_by_key(table_name, key, key_value, variable):
    table = dynamodb.Table(table_name)
    response = table.get_item(Key={key: key_value}, ProjectionExpression=variable)

    return response.get("Item", {}).get(variable, {})


def db_get_variables_by_key(table_name, key, key_value, variables):
    table = dynamodb.Table(table_name)

    response = table.get_item(Key={key: key_value}, ProjectionExpression=", ".join(variables))
    return response.get("Item", {})


def db_add_item(table_name, item):
    table = dynamodb.Table(table_name)
    try:
        response = table.put_item(Item=item)
        return response["ResponseMetadata"]["HTTPStatusCode"] == 200
    except Exception as e:
        logging.error(f"Error adding item: {e}; {item}")
        return False


def update_dynamodb_item(table_name, key_name, key_value, attribute_name, new_value):
    table = dynamodb.Table(table_name)
    try:
        response = table.update_item(
            Key={key_name: key_value},  # Specify the key to identify the item
            UpdateExpression=f"SET {attribute_name} = :val",  # Update the attribute
            ExpressionAttributeValues={":val": new_value},  # Provide new value
            ReturnValues="UPDATED_NEW",  # Return the updated value
        )
        return True if "Attributes" in response else False
    except Exception as e:
        logging.error(f"Error updating item: {e}")
        return False
