from app import app
import awsgi
from flask import Flask, jsonify
import json

def get_allowed_origin(event):
    # Get origin from headers
    headers = event.get("headers", {})
    origin = headers.get("origin", headers.get("Origin", ""))
    
    # List of allowed origins
    allowed_origins = [
        "http://localhost:3000",
        "https://www.drangue.ai",
        "https://drangue.ai",
        "https://palm.drangue.ai",
        "https://pineapple.drangue.ai",
        "*"
    ]
    
    # Return the origin if it's allowed, otherwise return default
    return origin if origin in allowed_origins else allowed_origins[0]

def lambda_handler(event, context):
    try:
        # Get the appropriate origin for CORS headers
        allowed_origin = get_allowed_origin(event)
        
        # Handle OPTIONS requests for CORS
        if event["requestContext"]["http"]["method"] == "OPTIONS":
            return {
                "statusCode": 204,
                "headers": {
                    "Access-Control-Allow-Origin": allowed_origin,
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
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Credentials": "true"
        })
        
        return response

    except KeyError as e:
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": allowed_origin,
                "Access-Control-Allow-Credentials": "true"
            },
            "body": json.dumps({"error": f"Missing key: {str(e)}"})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": allowed_origin,
                "Access-Control-Allow-Credentials": "true"
            },
            "body": json.dumps({"error": f"An unexpected error occurred: {str(e)}"})
        }