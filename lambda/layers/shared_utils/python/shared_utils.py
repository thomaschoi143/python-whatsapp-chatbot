import boto3
import json


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
