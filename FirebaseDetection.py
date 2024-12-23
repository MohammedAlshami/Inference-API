import requests
from PIL import Image, ImageDraw, ImageFont
import io
import numpy as np
import onnxruntime
from io import BytesIO




class FirebaseDetection:
    def __init__(self, firebase_config):
        # Initialize Firebase
        # self.firebase = pyrebase.initialize_app(firebase_config)
        # self.storage = self.firebase.storage()

        # Load ONNX models
        self.session_net = onnxruntime.InferenceSession("best.onnx")
        self.session_nms = onnxruntime.InferenceSession("nms-yolov8.onnx")

        # Predefined class labels
        self.class_labels = [
            "abnormal",    # Label 0
            "ripe",         # Label 1
            "underripe",    # Label 2
            "ripe",         # Label 3
            "unripe",       # Label 4
            "overripe"      # Label 5
        ]

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
        # Draw bounding boxes and labels on the image
        draw = ImageDraw.Draw(image)

        for detection in detections:
            bbox = detection['bbox']
            label_idx = detection['label']
            # Use the label_idx to map to the class label
            if label_idx < len(self.class_labels):
                label = self.class_labels[label_idx]
            else:
                label = "Unknown"

            center_x, center_y, width, height = bbox
            top_left_x = (center_x - width / 2) * image.width / 640
            top_left_y = (center_y - height / 2) * image.height / 640
            width = width * image.width / 640
            height = height * image.height / 640

            # Draw the bounding box
            draw.rectangle([top_left_x, top_left_y, top_left_x + width, top_left_y + height], outline="red", width=3)

            # Draw the label
            font = ImageFont.load_default()  # Use default font or specify a font file path
            text_width, text_height = draw.textsize(label, font=font)
            draw.text((top_left_x + width / 2 - text_width / 2, top_left_y - text_height), label, fill="red", font=font)

        # Save the image to a BytesIO object
        img_bytes = BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        return img_bytes

    # def upload_to_firebase(self, img_bytes, file_name):
    #     # Upload image to Firebase Storage
    #     self.storage.child(file_name).put(img_bytes)
    #     file_url = self.storage.child(file_name).get_url(None)
    #     return file_url

    def process_and_upload(self, image_url):
        image = self.download_image(image_url)
        # detections = self.detect_image(image)

        # img_bytes = self.plot_bboxes_with_labels(image, detections)

        # Generate a unique file name
        # file_name = "detected_image.png"

        # Upload to Firebase Storage
        # file_url = self.upload_to_firebase(img_bytes, file_name)
        file_url = "https://myhackathon1.vercel.app/detection_sample.png"

        return file_url
