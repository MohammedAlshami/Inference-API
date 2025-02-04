import base64
from ultralytics import YOLO
import cv2
import os
import numpy as np
import requests
from PIL import Image
from io import BytesIO

class YOLOSegmenter:
    MODELS = {
        "palm": {"segmentation": "models/palm/pt/palm_segmentation.pt", "ripeness": "models/palm/pt/palm_ripe.pt"},
        "pineapple": {"segmentation": "models/pineapple/pt/pineapple_segmentation.pt", "ripeness": "models/pineapple/pt/pineapple_ripe.pt"},
        "apple": {"segmentation": "models/apple/pt/apple_segmentation.pt", "ripeness": "models/apple/pt/apple_ripeness.pt"}
    }
    
    def __init__(self, model_name):
        if model_name not in self.MODELS:
            raise ValueError("Invalid model name. Choose from: palm, pineapple, apple")
        
        self.model = YOLO(self.MODELS[model_name]["segmentation"])
        self.ripeness_model = YOLO(self.MODELS[model_name]["ripeness"])

    def process_image(self, image_path, conf=0.3, segmentation=True, ripeness=True, legend=False, distance_cm=30):
        image = self.load_image(image_path)
        if image is None:
            return {"error": "Failed to load image"}
        
        measurements = []
        
        if segmentation:
            results = self.model(image, conf=conf)
            result = results[0]
            measurements = self.get_fruit_measurements(image, result, distance_cm)
            segmented_image = self.overlay_segmentation(image, result)
        else:
            segmented_image = image.copy()
        
        if ripeness:
            ripeness_results = self.ripeness_model(image, conf=conf)
            ripeness_levels = self.get_ripeness_levels(ripeness_results[0])
            for i in range(len(measurements)):
                measurements[i]["ripeness"] = ripeness_levels[i] if i < len(ripeness_levels) else "Unknown"
        
        if legend:
            segmented_image = self.add_legend(segmented_image, measurements)
        
        if not measurements:
            return {"error": "No objects detected", "input": image_path}
        
        # Convert the image to base64
        _, buffer = cv2.imencode(".jpg", segmented_image)
        base64_str = base64.b64encode(buffer).decode("utf-8")
        
        return {
            "detection_result_img": f'data:image/jpeg;base64,{base64_str}',
            "measurements": {
                "height": measurements[0]["height_cm"],
                "width": measurements[0]["width_cm"], 
                "area": measurements[0]["area_cm"],
                "ripeness": measurements[0].get("ripeness", "Unknown")
            }
        }
    def load_image(self, image_path):
        # Check if it's a base64-encoded image
        if image_path.startswith('data:image/'):
            # Split the base64 string and decode
            try:
                # Remove the data URL prefix and decode
                base64_str = image_path.split(',')[1]
                nparr = np.frombuffer(base64.b64decode(base64_str), np.uint8)
                return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            except Exception as e:
                print(f"Error decoding base64 image: {e}")
                return None
        
        # Check if it's a local file path
        if os.path.exists(image_path):
            return cv2.imread(image_path)
        
        # Check if it's a URL
        try:
            response = requests.get(image_path)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"Error loading image from URL: {e}")
        
        return None
    
    def get_fruit_measurements(self, image, results, distance_cm):
        img_height, img_width = image.shape[:2]
        cm_per_pixel = distance_cm / img_width  # Adjust measurement scale
        
        measurements = []
        
        if results.masks is not None:
            for mask in results.masks.xy:
                mask = np.array(mask, np.int32)
                x, y, w, h = cv2.boundingRect(mask)
                area_cm = round(w * h * cm_per_pixel ** 2, 2)
                measurements.append({
                    "width_cm": round(w * cm_per_pixel, 2),
                    "height_cm": round(h * cm_per_pixel, 2),
                    "area_cm": area_cm
                })
        
        return measurements
    
    def get_ripeness_levels(self, results):
        ripeness_levels = []
        
        if results.masks is not None:
            for mask in results.masks.xy:
                ripeness_levels.append("masked_data")
        elif results.boxes is not None:
            for box in results.boxes.data:
                ripeness_levels.append(int(box[-1]))
        
        return ripeness_levels
    
    def overlay_segmentation(self, image, results):
        mask_overlay = np.zeros_like(image, dtype=np.uint8)
        
        if results.masks is not None:
            for mask in results.masks.xy:
                mask = np.array(mask, np.int32)
                cv2.fillPoly(mask_overlay, [mask], (0, 255, 0))
        
        return cv2.addWeighted(image, 0.7, mask_overlay, 0.3, 0)
    
    def add_legend(self, image, measurements):
        y0, dy = 30, 40
        for i, m in enumerate(measurements):
            text = f"Fruit {i+1}: {m['width_cm']}cm x {m['height_cm']}cm, Area: {m['area_cm']}cm²"
            cv2.putText(image, text, (10, y0 + i * dy), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3, cv2.LINE_AA)
        return image
