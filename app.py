import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from InferencePipeline import InferencePipeline

app = Flask(__name__)

# Enable CORS
from flask_cors import CORS

# Enable CORS with explicit headers
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Origin"])

# Load environment variables
load_dotenv()

# Initialize inference pipeline
inferencePipeline = InferencePipeline()

from flask import make_response

@app.route('/detect', methods=['POST', 'OPTIONS'])
def detect():
    if request.method == 'OPTIONS':
        # Preflight response for CORS
        response = make_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Access-Control-Allow-Origin"
        return response, 200
    
    data = request.get_json()
    media_url = data.get('media_url')
    model_type = data.get('model_type')
    
    detection_result_img = inferencePipeline.process_and_upload(media_url, model_type)
    
    response = jsonify({'detection_result_img': detection_result_img})
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.route('/')
def home():
    return 'WhatsApp Bot is running!'
 
