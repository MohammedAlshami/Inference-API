from app import handler
import awsgi
from flask import Flask, jsonify
import json

def lambda_handler(event, context):
    try:
        # Standard API requests
        event["httpMethod"] = event["requestContext"]["http"]["method"]
        event["path"] = event["requestContext"]["http"]["path"]
        event["queryStringParameters"] = event.get("queryStringParameters", {})

        response = awsgi.response(handler, event, context)
        return response

    except KeyError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Missing key: {str(e)}"})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"An unexpected error occurred: {str(e)}"})
        }