# import os
# from flask import Flask, request, jsonify
# # from InferencePipeline import InferencePipeline
# from dotenv import load_dotenv
# from urllib.parse import urlparse
# import os
# from flask_cors import CORS

# app = Flask(__name__)

# # Enable CORS
# CORS(app)

# # inferencePipeline = InferencePipeline()


# # @app.route('/detect', methods=['POST'])
# # def detect():
# #     data = request.get_json()
# #     media_url = data['media_url']
# #     detection_result_img = inferencePipeline.process_and_upload(media_url)
# #     return jsonify({'detection_result_img': detection_result_img})

# @app.route('/')
# def home():
    
#     return 'WhatsApp Bot is running!'

# if __name__ == '__main__':
#     app.run(debug=True, port=5000)

import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from urllib.parse import urlparse
import os
from flask_cors import CORS
from aws_lambda_wsgi import render_request

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return 'WhatsApp Bot is running!'

def lambda_handler(event, context):
    """
    Lambda handler that transforms API Gateway event into WSGI request
    and processes it with Flask app
    """
    # Convert API Gateway event to WSGI request
    response = render_request(app, event, context)
    return response

if __name__ == '__main__':
    app.run(debug=True, port=5000)