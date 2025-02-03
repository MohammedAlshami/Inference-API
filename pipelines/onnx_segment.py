from ultralytics import YOLO
import cv2
import os
import numpy as np
import requests
from PIL import Image
from io import BytesIO

class YOLOSegmenter:
    def __init__(self, model_path):
        """
        Initialize YOLO segmenter.
        Args:
            model_path (str): Path to YOLO model file (.pt)
        """
        self.model = YOLO(model_path)

    def process_image(self, image_path, save_dir='output', conf=0.3):
        """
        Process image, segment objects, and estimate real-world sizes.
        Args:
            image_path (str): Path to image or URL
            save_dir (str): Directory to save results
            conf (float): Confidence threshold
        Returns:
            List of fruit measurements (width & height in cm)
        """
        os.makedirs(save_dir, exist_ok=True)  # Ensure output directory exists

        # Run YOLO segmentation
        results = self.model(image_path, conf=conf)
        result = results[0]

        # Load the original image
        image = self.load_image(image_path)

        if image is None:
            raise ValueError(f"Failed to load image from {image_path}")

        # Estimate real-world size
        measurements = self.get_fruit_measurements(image, result)

        # Overlay segmentation masks without bounding boxes
        segmented_image = self.overlay_segmentation(image, result)

        # Save output image
        output_path = os.path.join(save_dir, 'segmented_no_boxes.jpg')
        cv2.imwrite(output_path, segmented_image)

        # Print results
        for i, m in enumerate(measurements):
            print(f"Fruit {i+1}: Width = {m['width_cm']} cm, Height = {m['height_cm']} cm")

        return output_path, measurements

    def load_image(self, image_path):
        """
        Load an image from a file path or URL.
        Args:
            image_path (str): Path to local image or URL
        Returns:
            np.array: Loaded image in OpenCV format (BGR)
        """
        if os.path.exists(image_path):  # Local file
            return cv2.imread(image_path)
        else:  # URL
            response = requests.get(image_path)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        return None

    def get_fruit_measurements(self, image, results):
        """
        Estimate real-world width and height of each segmented object.
        Args:
            image (np.array): Original image
            results: YOLO model segmentation results
        Returns:
            List of fruit measurements (width & height in cm)
        """
        img_height, img_width = image.shape[:2]  # Get image dimensions
        cm_per_pixel = 35 / img_width  # Convert pixels to cm (assuming 30 cm distance)

        measurements = []  # Store measurements

        for mask in results.masks.xy:
            mask = np.array(mask, np.int32)
            x, y, w, h = cv2.boundingRect(mask)  # Get bounding box

            real_width_cm = w * cm_per_pixel
            real_height_cm = h * cm_per_pixel

            measurements.append({
                "width_cm": round(real_width_cm, 2),
                "height_cm": round(real_height_cm, 2)
            })

        return measurements

    def overlay_segmentation(self, image, results):
        """
        Overlay segmentation masks on an image without bounding boxes.
        Args:
            image (np.array): Original image
            results: YOLO model segmentation results
        Returns:
            np.array: Image with segmentation overlay
        """
        mask_overlay = np.zeros_like(image, dtype=np.uint8)  # Create blank overlay

        # Extract segmentation masks
        for mask in results.masks.xy:
            mask = np.array(mask, np.int32)
            cv2.fillPoly(mask_overlay, [mask], (0, 255, 0))  # Fill with green color

        # Blend original image with segmentation overlay
        blended = cv2.addWeighted(image, 0.7, mask_overlay, 0.3, 0)
        return blended

# Example usage
segmenter = YOLOSegmenter(r"C:\Users\USER\Desktop\Work\drangue\Repos\Light Inference API\models\apple_segemntation.pt")
output_path, measurements = segmenter.process_image(
    r"C:\Users\USER\Downloads\photo_2025-02-03_17-18-55.jpg",
    conf=0.3
)

print(f"Segmented image saved at: {output_path}")
