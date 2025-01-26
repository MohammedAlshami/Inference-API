from app import app
from awsgi import response

def lambda_handler(event, context):
    return response(app, event, context)
