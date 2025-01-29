import json
from app import app
import awsgi

def lambda_handler(event, context):
    event['httpMethod'] = event['requestContext']['http']['method']

    # ✅ Handle CORS preflight requests
    if event['httpMethod'] == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS, GET, POST",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            },
            "body": json.dumps({"message": "CORS preflight successful"})
        }

    # Pass request to Flask app
    response = awsgi.response(app, event, context)

    # ✅ Ensure JSON requests are allowed
    response["headers"]["Access-Control-Allow-Origin"] = "*"
    response["headers"]["Access-Control-Allow-Methods"] = "OPTIONS, GET, POST"
    response["headers"]["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

    return response
