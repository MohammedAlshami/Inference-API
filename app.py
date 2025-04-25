import json
import base64
import numpy as np
import cv2
import socket
import asyncio
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
from ultralytics import YOLO
import aiohttp

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://drangue.ai/"],  # Add other origins as needed
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Range", "X-Content-Range"],
        "supports_credentials": True
    }
})

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000", "http://drangue.ai/"])

# Global variables for models
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


async def load_models(model_type, detection_mode):
    """Load models based on type and mode."""
    global model_cache, current_model_type, current_detection_mode

    # If models are already loaded for this type and mode, return
    if (
        current_model_type == model_type
        and current_detection_mode == detection_mode
        and "segmentation" in model_cache
        and detection_mode in model_cache
    ):
        print(f"Models for {model_type}/{detection_mode} already loaded")
        return

    # Clear current models from memory
    model_cache = {}

    print(f"Loading models for {model_type}/{detection_mode}...")

    try:
        # Always load segmentation model
        segmentation_path = MODEL_TYPES[model_type]["paths"]["segmentation"]
        model_cache["segmentation"] = YOLO(segmentation_path)
        model_cache["segmentation"].to("cuda")

        # Load the specific detection model
        if detection_mode in MODEL_TYPES[model_type]["paths"]:
            detection_path = MODEL_TYPES[model_type]["paths"][detection_mode]
            model_cache[detection_mode] = YOLO(detection_path)
            model_cache[detection_mode].to("cuda")

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
        raise


def base64_to_image(base64_string):
    image_bytes = base64.b64decode(base64_string)
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    # Rotate image 180 degrees before processing
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


async def run_segmentation(image):
    if "segmentation" not in model_cache:
        return image  # Return original image if model not loaded

    try:
        segmentation_results = model_cache["segmentation"](
            image, conf=0.5, iou=0.2, save=False
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


async def run_detection(image, detection_mode):
    if detection_mode not in model_cache:
        return "Model not loaded"

    try:
        # Get class mapping for the current model type and detection mode
        classes = MODEL_TYPES[current_model_type]["classes"][detection_mode]

        detection_results = model_cache[detection_mode](image, conf=0.2, save=False)

        for detection_result in detection_results:
            if len(detection_result.boxes) > 0:
                boxes = detection_result.boxes
                class_ids = boxes.cls.cpu().numpy()
                confidences = boxes.conf.cpu().numpy()

                max_conf_idx = confidences.argmax()
                predicted_class_id = int(class_ids[max_conf_idx])

                # Debug log to check class ID
                print(
                    f"Detected class ID: {predicted_class_id} for {current_model_type}/{detection_mode}"
                )

                predicted_class = classes.get(predicted_class_id, "Unknown")
                confidence = confidences[max_conf_idx]

                return f"{predicted_class} (Confidence: {confidence:.2f})"

        return "Not Detected"
    except Exception as e:
        print(f"Error in detection: {e}")
        return f"Error: {str(e)}"


async def process_frame_data(data):
    try:
        # Extract image and basic data
        image = base64_to_image(data["image"])
        distance = data.get("distance", 0)
        camera_config = data.get("config")  # Get camera config if available

        # Get model selection data
        model_type = data.get("model_type", "pineapple")  # Default to pineapple
        detection_mode = data.get("detection_mode", "ripeness")  # Default to ripeness

        # Log the model selection
        print(f"Processing frame with model: {model_type}/{detection_mode}")

        # Ensure models are loaded
        await load_models(model_type, detection_mode)

        # Process image
        segmentation_future = asyncio.create_task(run_segmentation(image))
        detection_future = asyncio.create_task(run_detection(image, detection_mode))

        # Wait for both tasks to complete
        segmentation_image = await segmentation_future
        detection_result = await detection_future

        # Prepare response
        processed_base64 = image_to_base64(segmentation_image)

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
        response["available_modes"] = MODEL_TYPES[model_type]["modes"]

        return response
    except Exception as e:
        print(f"Error processing frame: {e}")
        return {
            "error": f"Error processing frame: {str(e)}",
            "camera_config": data.get("config"),
            "model_type": data.get("model_type", "pineapple"),
            "detection_mode": data.get("detection_mode", "ripeness"),
        }


@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")


@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")


@socketio.on('frame')
async def handle_frame(data):
    """Handle frame data from client"""
    try:
        # Create an event loop for the async process
        result = await process_frame_data(data)
        # Emit the processed result back to the client
        socketio.emit('processed_frame', result, room=request.sid)
    except Exception as e:
        print(f"Error handling frame from {request.sid}: {e}")
        socketio.emit('error', {"error": str(e)}, room=request.sid)


# Removed async get_public_ip function as it's not needed in Lambda environment


def get_local_ip():
    """Get the local IP address of this server."""
    try:
        # Get the hostname
        hostname = socket.gethostname()
        # Get the local IP address
        local_ip = socket.gethostbyname(hostname)
        return local_ip
    except Exception as e:
        print(f"Error getting local IP: {e}")
        return "127.0.0.1"


@app.route('/info')
def server_info():
    """Return information about the server and available models"""
    return jsonify({
        "models": MODEL_TYPES,
        "local_ip": get_local_ip()
    })

