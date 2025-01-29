from app import app
import awsgi
from flask import Flask, jsonify
import json

def lambda_handler(event, context):
    try:
        event['httpMethod'] = event['requestContext']['http']['method']
        event['path'] = event['requestContext']['http']['path']
        event['queryStringParameters'] = event.get('queryStringParameters', {})
        
        # Process the request and generate response
        response = awsgi.response(app, event, context)
        
        # Add CORS headers
        response["headers"]["Access-Control-Allow-Origin"] = "*"
        response["headers"]["Access-Control-Allow-Methods"] = "OPTIONS, GET, POST"
        response["headers"]["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        return response
    
    except KeyError as e:
        # Handle missing keys in the event dictionary
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Missing key: {str(e)}"})
        }
    
    except Exception as e:
        # Handle any other unexpected errors
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"An unexpected error occurred: {str(e)}"})
        }
