import cv2
import numpy as np
import requests
from PIL import Image
import io
import base64
import numpy as np
import onnxruntime
from io import BytesIO


class InferencePipeline:
    def __init__(self):
        # Initialize Firebase
        # Load ONNX models
        
        self.models = {
            "pineapple": onnxruntime.InferenceSession("models/pineapple.onnx"), 
             "palm": onnxruntime.InferenceSession("models/palm.onnx"),
             "pineapple-disease": onnxruntime.InferenceSession("models/pineapple-disease.onnx")
                  
                  }
        self.session_nms = onnxruntime.InferenceSession("models/nms-yolov8.onnx")


        self.labels = {
            "pineapple": ["Ripe", "Semi Ripe", "Raw"],
            "palm": [
            "abnormal",    # Label 0
            "ripe",         # Label 1
            "underripe",    # Label 2
            "ripe",         # Label 3
            "unripe",       # Label 4
            "overripe"      # Label 5
        ],
            "pineapple-disease": ['Crown_Rot_Disease', 'Fruit_Fasciation_Disorder', 'Fruit_Rot_Disease', 'Mealybug_Wilt_Disease', 'Multiple_Crown_Disorder', 'No_Disease', 'Root_Rot_Disease']
        }



    def download_image(self, image_url):
        # Download image from URL
        response = requests.get(image_url)
        image = Image.open(io.BytesIO(response.content))
        return image

    def detect_image(self, image):
        # Model parameters
        MODEL_SHAPES = [1, 3, 640, 640]  # Batch size, channels, height, width
        IOU_THRESHOLD = 0.45
        SCORE_THRESHOLD = 0.2
        
        model_width, model_height = MODEL_SHAPES[2], MODEL_SHAPES[3]
        
        # Resize the image to fit the model
        image_resized = image.resize((model_width, model_height))
        input_data = np.array(image_resized).astype(np.float32) / 255.0
        input_data = input_data.transpose(2, 0, 1)
        input_data = np.expand_dims(input_data, axis=0)

        # Create the input tensor
        tensor = onnxruntime.OrtValue.ortvalue_from_numpy(input_data)
        config = np.array([100, IOU_THRESHOLD, SCORE_THRESHOLD], dtype=np.float32)

        # Run inference
        outputs = self.session_net.run(None, {"images": tensor})
        detection_output = outputs[0]  # The first output is the detection result
        selected = self.session_nms.run(None, {"detection": detection_output, "config": config})[0]

        detections = []

        # Post-process selected detections
        for idx in range(selected.shape[1]):
            data = selected[0, idx, :]

            center_x, center_y, width, height = data[:4]
            scores = data[4:]

            # Find the class label with the highest confidence score
            max_score = -np.inf
            label = -1
            for i, score in enumerate(scores):
                if score > max_score:
                    max_score = score
                    label = i

            detections.append({
                "label": label,
                "confidence": max_score,
                "bbox": [center_x, center_y, width, height]
            })

        return detections

    def plot_bboxes_with_labels(self, image, detections):
        # Convert PIL Image to OpenCV format (BGR)
        image_cv = np.array(image)
        image_cv = image_cv[:, :, ::-1].copy()

        for detection in detections:
            bbox = detection['bbox']
            label_idx = detection['label']
            # Use the label_idx to map to the class label
            if label_idx < len(self.class_labels):
                label = self.class_labels[label_idx]
            else:
                label = "Unknown"

            center_x, center_y, width, height = bbox
            top_left_x = int((center_x - width / 2) * image.width / 640)
            top_left_y = int((center_y - height / 2) * image.height / 640)
            width = int(width * image.width / 640)
            height = int(height * image.height / 640)

            # Draw the bounding box
            cv2.rectangle(image_cv, (top_left_x, top_left_y), (top_left_x + width, top_left_y + height), (0, 0, 255), 2)

            # Add label text
            cv2.putText(image_cv, label, (top_left_x, top_left_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # Save the image to a BytesIO object
        _, img_bytes = cv2.imencode('.png', image_cv)
        img_bytes = BytesIO(img_bytes)

        return img_bytes



    def process_and_upload(self, media_input, model_type):
        """
        Process either an image URL or blob data and return the detected image as blob
        
        Args:
            media_input: Can be either a URL string or blob/base64 data
            
        Returns:
            dict: Contains the detected image as base64 string
        """
        
        # First determine if input is URL or blob data
        if isinstance(media_input, str) and (media_input.startswith('http://') or media_input.startswith('https://')):
            # Handle URL case
            image = self.download_image(media_input)
        else:
            # Handle blob/base64 case
            image = self.convert_blob_to_image(media_input)


        self.session_net = self.models[model_type]
        self.class_labels = self.labels[model_type]
        detections = self.detect_image(image)
        img_bytes = self.plot_bboxes_with_labels(image, detections)
        
        # Convert to base64
        base64_image = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
        
        return f'data:image/jpeg;base64,{base64_image}'

    def convert_blob_to_image(self, blob_data):
        """
        Convert blob data to PIL Image
        
        Args:
            blob_data: Binary blob data or base64 string
            
        Returns:
            PIL.Image: Converted image
        """
        try:
            # If it's base64 data
            if isinstance(blob_data, str):
                # Remove data URL prefix if present
                if 'base64,' in blob_data:
                    blob_data = blob_data.split('base64,')[1]
                
                # Decode base64 to bytes
                blob_data = base64.b64decode(blob_data)

            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(blob_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image

        except Exception as e:
            raise ValueError(f"Failed to convert blob data to image: {str(e)}")