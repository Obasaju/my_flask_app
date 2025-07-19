# db.py
import boto3
from botocore.exceptions import ClientError

# Specify region if needed
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table_name = 'Tasks'

def get_todo_table():
    try:
        table = dynamodb.Table(table_name)
        table.load()  # Ensure the table exists
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'id', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            table.wait_until_exists()
            return table
        else:
            raise
