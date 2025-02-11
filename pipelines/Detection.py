from ultralytics import YOLO
import cv2
import numpy as np
import base64
import requests
from PIL import Image
import io

class Detection:
    MODEL_PATHS = {
        "palm": {
            "segmentation": "models/palm/pt/palm_segmentation.pt",
            "ripeness": "models/palm/pt/palm_ripe.pt"
        },
        "pineapple": {
            "segmentation": "models/pineapple/pt/pineapple_segmentation.pt",
            "ripeness": "models/pineapple/pt/pineapple_ripe.pt"
        }
    }

    def __init__(self):
        """Initialize all models at startup"""
        self.models = {
            "palm": {
                "segmentation": YOLO(self.MODEL_PATHS["palm"]["segmentation"]),
                "ripeness": YOLO(self.MODEL_PATHS["palm"]["ripeness"])
            },
            "pineapple": {
                "segmentation": YOLO(self.MODEL_PATHS["pineapple"]["segmentation"]),
                "ripeness": YOLO(self.MODEL_PATHS["pineapple"]["ripeness"])
            }
        }

    def _validate_image(self, img):
        """Validate image dimensions and content"""
        if img is None:
            raise ValueError("Failed to load image")
        if img.size == 0:
            raise ValueError("Image is empty")
        if len(img.shape) != 3:
            raise ValueError("Image should have 3 channels")
        return True

    def _load_image_from_base64(self, base64_string):
        """Convert base64 string to image"""
        try:
            # Remove data URL prefix if present
            if 'base64,' in base64_string:
                base64_string = base64_string.split('base64,')[1]
            
            # Decode base64 string
            img_data = base64.b64decode(base64_string)
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if not self._validate_image(img):
                raise ValueError("Invalid image format")
            return img
            
        except Exception as e:
            raise ValueError(f"Error decoding base64 image: {str(e)}")

    def _load_image_from_url(self, url):
        """Download image from URL"""
        try:
            response = requests.get(url)
            response.raise_for_status()
            nparr = np.frombuffer(response.content, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if not self._validate_image(img):
                raise ValueError("Invalid image format")
            return img
            
        except Exception as e:
            raise ValueError(f"Error downloading image from URL: {str(e)}")

    def _image_to_base64(self, img):
        """Convert OpenCV image to base64 string with data URL prefix"""
        try:
            self._validate_image(img)
            _, buffer = cv2.imencode('.jpg', img)
            base64_string = base64.b64encode(buffer).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_string}"
        except Exception as e:
            raise ValueError(f"Error encoding image to base64: {str(e)}")


    def segment_image(self, image_input, fruit_type):
        """Perform segmentation on the input image"""
        try:
            if fruit_type not in self.models:
                raise ValueError(f"Unsupported fruit type: {fruit_type}")

            # Load image based on input type
            if isinstance(image_input, str):
                if image_input.startswith(('http://', 'https://')):
                    img = self._load_image_from_url(image_input)
                else:
                    img = self._load_image_from_base64(image_input)
            else:
                raise ValueError("Image input must be URL or base64 string")

            # Validate image dimensions
            self._validate_image(img)
            height, width = img.shape[:2]

            # Run segmentation with appropriate model
            results = self.models[fruit_type]["segmentation"](img)
            
            # Draw segmentation masks on the image
            for r in results:
                masks = r.masks
                if masks is not None:
                    for mask in masks:
                        # Convert mask to numpy array and validate
                        mask_array = mask.data.cpu().numpy()
                        if mask_array.size == 0:
                            continue
                            
                        # Ensure mask dimensions match image dimensions
                        if mask_array.shape[-2:] != (height, width):
                            mask_array = cv2.resize(mask_array.squeeze(), (width, height))
                            mask_array = mask_array[np.newaxis, :, :]

                        # Create and apply color mask
                        color_mask = np.zeros_like(img)
                        mask_array = mask_array.squeeze()
                        color_mask[mask_array > 0.5] = [0, 255, 0]  # Green overlay
                        img = cv2.addWeighted(img, 0.7, color_mask, 0.3, 0)

            # Convert the segmented image to base64
            img_base64 = self._image_to_base64(img)
            
            return {
                'segmented_image': img_base64,
                'num_objects': len(results[0].boxes) if results[0].boxes is not None else 0
            }
        except Exception as e:
            raise ValueError(f"Segmentation error: {str(e)}")

    def detect_ripeness(self, image_input, fruit_type):
        """Detect ripeness of the fruit in the image"""
        try:
            if fruit_type not in self.models:
                raise ValueError(f"Unsupported fruit type: {fruit_type}")

            # Define classes for each fruit type
            classes = {
                "palm": {0: 'Ripe', 1: 'Semi_Ripe', 2: 'Un_Ripe'},
                "pineapple": {0: 'Ripe', 1: 'Semi_Ripe', 2: 'Un_Ripe'}
            }

            # Load image based on input type
            if isinstance(image_input, str):
                if image_input.startswith(('http://', 'https://')):
                    img = self._load_image_from_url(image_input)
                else:
                    img = self._load_image_from_base64(image_input)
            else:
                raise ValueError("Image input must be URL or base64 string")

            # Validate image
            self._validate_image(img)

            # Run ripeness detection with appropriate model
            results = self.models[fruit_type]["ripeness"](img, conf=0.2)
            
            # Process results
            for result in results:
                if len(result.boxes) > 0:
                    # Get the boxes, class IDs and confidence scores
                    boxes = result.boxes
                    class_ids = boxes.cls.cpu().numpy()  # Get class IDs
                    confidences = boxes.conf.cpu().numpy()  # Get confidence scores
                    
                    # Get prediction with highest confidence
                    max_conf_idx = confidences.argmax()
                    predicted_class_id = int(class_ids[max_conf_idx])
                    confidence = float(confidences[max_conf_idx])
                    
                    # Map class ID to class name
                    predicted_class = classes[fruit_type].get(predicted_class_id, "Unknown")
                    
                    return {
                        'ripeness': predicted_class,
                        'confidence': confidence
                    }
            
            return {
                'ripeness': 'Unknown',
                'confidence': 0.0
            }
        except Exception as e:
            raise ValueError(f"Ripeness detection error: {str(e)}")

    def process_image(self, image_input, fruit_type):
        """Process image through both segmentation and ripeness detection"""
        try:
            # Validate fruit type
            if fruit_type not in self.models:
                raise ValueError(f"Unsupported fruit type: {fruit_type}")

            # Perform both operations
            seg_results = self.segment_image(image_input, fruit_type)
            ripe_results = self.detect_ripeness(image_input, fruit_type)
            
            # Combine results
            return {
                'status': 'success',
                'detection_result_img': seg_results['segmented_image'],
                'num_objects': seg_results['num_objects'],
                'ripeness': ripe_results['ripeness'],
                'confidence': ripe_results['confidence']
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }