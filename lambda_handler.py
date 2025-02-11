from app import handler
import awsgi
from flask import Flask, jsonify
import json

def lambda_handler(event, context):
    """
    AWS Lambda handler function that processes API Gateway requests
    using the Mangum handler.
    """
    try:
        response = handler(event, context)
        return response
    except Exception as e:
        return {
            "statusCode": 500,
            "body": {
                "error": f"An unexpected error occurred: {str(e)}"
            }
        }