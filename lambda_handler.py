from app import app
import awsgi
from flask import Flask, jsonify
import json

def lambda_handler(event, context):
    try:
        # Handle OPTIONS requests for CORS
        if event["requestContext"]["http"]["method"] == "OPTIONS":
            return {
                "statusCode": 204,
                "headers": {
                    "Access-Control-Allow-Origin": origin if origin in ["http://localhost:3000", "http://drangue.ai"] else "http://localhost:3000",
                    "Access-Control-Allow-Headers": "Content-Type,Authorization",
                    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Expose-Headers": "Content-Range,X-Content-Range"
                }
            }

        # Standard API requests
        event["httpMethod"] = event["requestContext"]["http"]["method"]
        event["path"] = event["requestContext"]["http"]["path"]
        event["queryStringParameters"] = event.get("queryStringParameters", {})

        response = awsgi.response(app, event, context)
        
        # Add CORS headers to the response
        if "headers" not in response:
            response["headers"] = {}
            
        response["headers"].update({
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Credentials": "true"
        })
        
        return response

    except KeyError as e:
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Credentials": "true"
            },
            "body": json.dumps({"error": f"Missing key: {str(e)}"})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Credentials": "true"
            },
            "body": json.dumps({"error": f"An unexpected error occurred: {str(e)}"})
        }
