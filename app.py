from flask import Flask, request, jsonify
import json
import base64
import numpy as np
import cv2
from ultralytics import YOLO
# Removed asyncio, websockets, aiohttp, socket as they are not used by Flask's HTTP server


# Global variables for models
# Note: In a multi-threaded or multi-process Flask setup (common with production servers),
# this global cache might need more sophisticated handling (e.g., thread-local storage or
# a manager process) to avoid race conditions or redundant loading across workers.
# For simple 'flask run', this is usually sufficient.
model_cache = {}
current_model_type = None
current_detection_mode = None

# Define available model types
MODEL_TYPES = {
    "pineapple": {
        "modes": ["ripeness"],
        "paths": {
            "segmentation": "models/pineapple/pt/pineapple_segmentation.pt",
            "ripeness": "models/pineapple/pt/pineapple_ripe.pt",
        },
        "classes": {"ripeness": {0: "Ripe", 1: "Semi_Ripe", 2: "Un_Ripe"}},
    },
    "palm": {
        "modes": ["ripeness", "pollination"],
        "paths": {
            "segmentation": "models/palm/pt/palm_segmentation.pt",
            "ripeness": "models/palm/pt/palm_ripeness.pt",
            "pollination": "models/palm/pt/palm_pollination.pt",  # This will be disabled in UI
        },
        "classes": {
            # Updated palm oil ripeness classes to match actual model output
            "ripeness": {0: "Slightly unripe", 1: "Ripe", 2: "Unripe", 3: "Overripe"},
            "pollination": {0: "Pollinated", 1: "Not_Pollinated"},
        },
    },
}

# Initialize Flask app
app = Flask(__name__)

# Synchronous function to load models
def load_models(model_type, detection_mode):
    """Load models based on type and mode."""
    global model_cache, current_model_type, current_detection_mode

    # Input validation
    if model_type not in MODEL_TYPES:
        raise ValueError(f"Invalid model_type: {model_type}")
    if detection_mode not in MODEL_TYPES[model_type]["modes"]:
         raise ValueError(f"Invalid detection_mode: {detection_mode} for model_type {model_type}")


    # If models are already loaded for this type and mode, return
    if (
        current_model_type == model_type
        and current_detection_mode == detection_mode
        and "segmentation" in model_cache
        and detection_mode in model_cache
    ):
        # print(f"Models for {model_type}/{detection_mode} already loaded") # Optional: keep logging
        return

    # Clear current models from memory
    model_cache = {}

    print(f"Loading models for {model_type}/{detection_mode}...")

    try:
        # Always load segmentation model
        segmentation_path = MODEL_TYPES[model_type]["paths"]["segmentation"]
        model_cache["segmentation"] = YOLO(segmentation_path)
        # model_cache["segmentation"].to("cuda") # Use .to('cuda') if a GPU is available

        # Load the specific detection model
        detection_path = MODEL_TYPES[model_type]["paths"][detection_mode]
        model_cache[detection_mode] = YOLO(detection_path)
        # model_cache[detection_mode].to("cuda") # Use .to('cuda') if a GPU is available


        # Update current model type and mode
        current_model_type = model_type
        current_detection_mode = detection_mode

        print(f"Models for {model_type}/{detection_mode} loaded successfully!")
    except Exception as e:
        print(f"Error loading models: {e}")
        # Reset cache if loading fails
        model_cache = {}
        current_model_type = None
        current_detection_mode = None
        raise # Re-raise the exception so the route handler can catch it


def base64_to_image(base64_string):
    image_bytes = base64.b64decode(base64_string)
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image from base64")
    # Rotate image 180 degrees before processing (optional, based on camera orientation)
    image = cv2.rotate(image, cv2.ROTATE_180)
    return image


def image_to_base64(image):
    # Use lower JPEG quality (90 instead of default 95) for faster encoding
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, 90]
    success, encoded_image = cv2.imencode(".jpg", image, encode_params)
    if not success:
        return None
    base64_string = base64.b64encode(encoded_image.tobytes()).decode("utf-8")
    return base64_string


# Synchronous segmentation function
def run_segmentation(image):
    if "segmentation" not in model_cache:
        print("Segmentation model not loaded, skipping segmentation.")
        return image  # Return original image if model not loaded

    try:
        # Run inference
        segmentation_results = model_cache["segmentation"](
            image, conf=0.5, iou=0.2, save=False, verbose=False # Set verbose=False for less output
        )
        segmentation_result = segmentation_results[0]

        # Check if there are any detections
        if len(segmentation_result.boxes) == 0:
            print("No segmentation detections found")
            return image

        # Plot the segmentation result
        segmentation_plotted_image = segmentation_result.plot()
        return segmentation_plotted_image
    except Exception as e:
        print(f"Error in segmentation: {e}")
        return image  # Return original image on error


# Synchronous detection function
def run_detection(image, detection_mode):
    if detection_mode not in model_cache:
        print(f"Detection model '{detection_mode}' not loaded, skipping detection.")
        return "Model not loaded"

    try:
        # Get class mapping for the current model type and detection mode
        # Ensure current_model_type and detection_mode are valid before accessing MODEL_TYPES
        if current_model_type not in MODEL_TYPES or \
           detection_mode not in MODEL_TYPES[current_model_type]["classes"]:
            return "Invalid model type or detection mode configuration"

        classes = MODEL_TYPES[current_model_type]["classes"][detection_mode]

        # Run inference
        detection_results = model_cache[detection_mode](image, conf=0.2, save=False, verbose=False) # Set verbose=False

        # Process results - assuming one primary detection per frame is needed
        # Modify this logic if multiple detections should be returned
        for detection_result in detection_results:
            if len(detection_result.boxes) > 0:
                boxes = detection_result.boxes
                confidences = boxes.conf.cpu().numpy()

                # Find the detection with the highest confidence
                max_conf_idx = confidences.argmax()
                predicted_class_id = int(boxes.cls.cpu().numpy()[max_conf_idx])
                confidence = confidences[max_conf_idx]

                # Get class name from mapping, default to 'Unknown'
                predicted_class = classes.get(predicted_class_id, f"Unknown Class ID: {predicted_class_id}")

                # print(f"Detected class: {predicted_class} (Conf: {confidence:.2f})") # Optional: keep logging

                return f"{predicted_class} (Confidence: {confidence:.2f})"

        return "Not Detected" # Return this if no boxes were detected above confidence threshold
    except Exception as e:
        print(f"Error in detection: {e}")
        return f"Error during detection: {str(e)}"

# Flask Route to handle image processing requests
@app.route('/process_image', methods=['POST'])
def process_image_route():
    """
    Handles POST requests to process an image.
    Expects a JSON body with:
    {
        "image": "base64_encoded_image_string",
        "model_type": "pineapple" or "palm",
        "detection_mode": "ripeness" or "pollination" (depends on model_type),
        "distance": optional numerical value,
        "config": optional configuration object
    }
    """
    data = request.json

    # Basic input validation
    if not data:
        return jsonify({"error": "No JSON data received"}), 400
    if "image" not in data or not isinstance(data["image"], str):
        return jsonify({"error": "Missing or invalid 'image' field (must be base64 string)"}), 400

    # Get model selection data with defaults
    model_type = data.get("model_type", "pineapple").lower() # Ensure lowercase for dictionary lookup
    detection_mode = data.get("detection_mode", "ripeness").lower() # Ensure lowercase

    distance = data.get("distance", 0)
    camera_config = data.get("config")

    print(f"Received request for model: {model_type}/{detection_mode}")

    try:
        # Ensure models are loaded for the requested type and mode
        load_models(model_type, detection_mode)

        # Decode image
        image = base64_to_image(data["image"])
        if image is None:
            return jsonify({"error": "Failed to decode base64 image"}), 400

        # Process image (segmentation and detection run sequentially)
        segmentation_image = run_segmentation(image)
        detection_result = run_detection(image, detection_mode)

        # Encode processed image back to base64
        processed_base64 = image_to_base64(segmentation_image)
        if processed_base64 is None:
             # Still return detection result even if encoding failed
             return jsonify({
                 "error": "Failed to encode processed image",
                 "camera_config": camera_config,
                 "model_type": model_type,
                 "detection_mode": detection_mode,
                 "distance": distance,
                 detection_mode: detection_result, # Include detection result
                 "available_modes": MODEL_TYPES.get(model_type, {}).get("modes", [])
             }), 500


        # Build response object
        response = {
            "processed_image": processed_base64,
            "camera_config": camera_config,
            "model_type": model_type,
            "detection_mode": detection_mode,
            "distance": distance,
        }

        # Add detection result with the appropriate key based on mode
        response[detection_mode] = detection_result

        # Include available modes for the current model type
        response["available_modes"] = MODEL_TYPES.get(model_type, {}).get("modes", [])


        # Return the response as JSON
        return jsonify(response), 200

    except ValueError as ve:
         print(f"Validation Error: {ve}")
         return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error processing request: {e}")
        # Return an error response with details
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "camera_config": camera_config,
            "model_type": model_type,
            "detection_mode": detection_mode,
            "distance": distance,
            "available_modes": MODEL_TYPES.get(model_type, {}).get("modes", [])
        }), 500

# Optional: Add a root route for basic server status check
@app.route('/')
def index():
    return "AI Processing Server (Flask) is running!"

# Remove the if __name__ == "__main__": block.
# To run this:
# 1. Save the code as a Python file (e.g., app.py).
# 2. Make sure you have flask installed (`pip install Flask opencv-python ultralytics`).
# 3. Make sure your model files exist at the specified paths (e.g., models/pineapple/pt/pineapple_segmentation.pt).
# 4. Open your terminal in the directory where you saved the file.
# 5. Run the command: `flask run --host=0.0.0.0 --port=5000` (or any desired port).
#    `--host=0.0.0.0` makes the server accessible from other machines on your network.