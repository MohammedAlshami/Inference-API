from app import app
import awsgi
from flask import Flask, jsonify
import json

def lambda_handler(event, context):
    # Handle OPTIONS preflight request
    if event['requestContext']['http']['method'] == 'OPTIONS':
        return {
            'statusCode': 204,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST,OPTIONS,GET'
            }
        }
    
    event['httpMethod'] = event['requestContext']['http']['method']
    event['path'] = event['requestContext']['http']['path']
    event['queryStringParameters'] = event.get('queryStringParameters', {})
    
    response = awsgi.response(app, event, context)
    
    # Add CORS headers to the response
    if 'headers' not in response:
        response['headers'] = {}
        
    response['headers'].update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST,OPTIONS,GET'
    })
    
    return response