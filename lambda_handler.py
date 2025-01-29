# from app import app
from app import app


import awsgi
from flask import Flask, jsonify
import json


def lambda_handler(event, context):
    event['httpMethod'] = event['requestContext']['http']['method']
    event['path'] = event['requestContext']['http']['path']
    event['queryStringParameters'] = event.get('queryStringParameters', {})
    
    response = awsgi.response(app, event, context)
    response["headers"]["Access-Control-Allow-Origin"] = "*"
    response["headers"]["Access-Control-Allow-Methods"] = "OPTIONS, GET, POST"
    response["headers"]["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response