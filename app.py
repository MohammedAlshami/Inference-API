import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
# from pipelines.InferencePipeline import InferencePipeline
from pipelines.YOLOSegmenter import YOLOSegmenter

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Initialize inference pipeline
# inferencePipeline = InferencePipeline()

# @app.route('/detect', methods=['POST', 'GET'])
# def detect():
#     data = request.get_json()
#     media_url = data.get('media_url')
#     model_type = data.get('model_type')
    
#     print(f"Model Type: {model_type}")
    
#     # Process and upload using inference pipeline
#     detection_result_img = inferencePipeline.process_and_upload(media_url, model_type)
#     return jsonify({'detection_result_img': detection_result_img})

@app.route('/segment', methods=['POST'])
def segment():
    data = request.get_json()
    image_path = data.get('image_path')
    model_type = data.get('model_type')
    distance = data.get('distance', 30)  # Default distance is 30cm
    confidence = data.get('confidence', 0.3)
    
    segmenter = YOLOSegmenter(model_type)
    result = segmenter.process_image(image_path, segmentation=True, ripeness=True, conf=confidence, legend=True, distance_cm=distance)
    return jsonify(result)

@app.route('/')
def home():
    return 'WhatsApp Bot is running!'

if __name__ == '__main__':
    app.run(debug=True)
