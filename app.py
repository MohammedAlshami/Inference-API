import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from pipelines.YOLOSegmenter import YOLOSegmenter
from pipelines.Detection import Detection

app = Flask(__name__)

# Enable CORS for all origins
CORS(app, resources={r"/*": {"origins": "*"}})

# Load environment variables
load_dotenv()

detector = Detection()

@app.route('/detect', methods=['POST'])
def detect():
    # Get JSON data from request
    data = request.get_json()
    
    # Validate required fields
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
    image_input = data.get('image')
    fruit_type = data.get('fruit_type')
    
    if not image_input:
        return jsonify({'status': 'error', 'message': 'No image provided'}), 400
    
    if not fruit_type:
        return jsonify({'status': 'error', 'message': 'No fruit type specified'}), 400
        
    try:
        # Process the image with specified fruit type
        results = detector.process_image(image_input, fruit_type)
        return jsonify(results)
        
    except ValueError as ve:
        return jsonify({'status': 'error', 'message': str(ve)}), 400
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

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
    app.run(debug=True, host='0.0.0.0', port=5000)