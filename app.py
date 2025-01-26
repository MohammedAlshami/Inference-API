import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
# from InferencePipeline import InferencePipeline

app = Flask(__name__)

# Enable CORS
CORS(app)

# Load environment variables
load_dotenv()

# Initialize inference pipeline
# inferencePipeline = InferencePipeline()

# @app.route('/detect', methods=['POST'])
# def detect():
#     data = request.get_json()
#     media_url = data.get('media_url')
#     model_type = data.get('model_type')
    
#     print(f"Model Type: {model_type}")
    
#     # Process and upload using inference pipeline
#     detection_result_img = inferencePipeline.process_and_upload(media_url, model_type)
#     return jsonify({'detection_result_img': detection_result_img})

@app.route('/')
def home():
    return 'WhatsApp Bot is running!'
