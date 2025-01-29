from app import app
import awsgi
from flask import Flask, jsonify
import json

def lambda_handler(event, context):
    try:
        # Handle preflight requests (CORS preflight)
        if event["requestContext"]["http"]["method"] == "OPTIONS":
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "OPTIONS, GET, POST",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization"
                },
                "body": json.dumps({"message": "CORS preflight success"})
            }

        # Standard API requests
        event["httpMethod"] = event["requestContext"]["http"]["method"]
        event["path"] = event["requestContext"]["http"]["path"]
        event["queryStringParameters"] = event.get("queryStringParameters", {})

        response = awsgi.response(app, event, context)

        # Add CORS headers
        response["headers"]["Access-Control-Allow-Origin"] = "*"
        response["headers"]["Access-Control-Allow-Methods"] = "OPTIONS, GET, POST"
        response["headers"]["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

        return response

    except KeyError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Missing key: {str(e)}"}),
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS, GET, POST",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"An unexpected error occurred: {str(e)}"}),
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS, GET, POST",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        }
