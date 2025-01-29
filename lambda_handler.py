# from app import app
# from awsgi import response

# def lambda_handler(event, context):
#     # Add error handling for missing httpMethod
#     if 'httpMethod' not in event:
#         # Log the event for debugging
#         print(f"Received event without httpMethod: {event}")
        
#         # Return a default response or raise a specific error
#         return {
#             'statusCode': 400,
#             'body': 'Invalid event: Missing httpMethod'
#         }
    
#     # Original handler logic
#     return response(app, event, context)


import awsgi
from flask import (
    Flask,
    jsonify,
)

app = Flask(__name__)


@app.route('/')
def index():
    return jsonify(status=200, message='Hello Flask!')


def lambda_handler(event, context):
    return awsgi.response(app, event, context)