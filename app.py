# import os
# from flask import Flask, request, jsonify
# from InferencePipeline import InferencePipeline
# from dotenv import load_dotenv
# from urllib.parse import urlparse
# import os
# from flask_cors import CORS

# app = Flask(__name__)

# # Enable CORS
# CORS(app)

# inferencePipeline = InferencePipeline()


# @app.route('/detect', methods=['POST'])
# def detect():
#     data = request.get_json()
#     media_url = data['media_url']
#     model_type = data['model_type']
#     print(model_type)
#     detection_result_img = inferencePipeline.process_and_upload(media_url, model_type)
#     return jsonify({'detection_result_img': detection_result_img})

# @app.route('/')
# def home():
    
#     return 'WhatsApp Bot is running!'

# if __name__ == '__main__':
#     app.run(debug=True, port=5000)

def handler(event, context):
    return 'Hello AWS Lambda'