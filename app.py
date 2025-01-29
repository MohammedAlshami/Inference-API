from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from InferencePipeline import InferencePipeline

app = Flask(__name__)

# Enable CORS with specific settings
CORS(app, resources={
    r"/*": {
        "origins": "*",  # Allow all origins
        "methods": ["POST", "OPTIONS", "GET"],
        "allow_headers": ["Content-Type"]
    }
})

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')  # Allow all origins
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS,GET')
    return response

# Rest of your code remains the same
@app.route('/detect', methods=['POST', 'OPTIONS'])
def detect():
    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 204
        
    data = request.get_json()
    media_url = data.get('media_url')
    model_type = data.get('model_type')
    
    print(f"Model Type: {model_type}")
    
    # Process and upload using inference pipeline
    detection_result_img = inferencePipeline.process_and_upload(media_url, model_type)
    return jsonify({'detection_result_img': detection_result_img})

@app.route('/')
def home():
    return 'WhatsApp Bot is running!'