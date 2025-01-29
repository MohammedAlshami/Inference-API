import cv2
import numpy as np
import matplotlib.pyplot as plt

roi_coords = []
click_count = 0

# Constants for iPhone 14 Plus Camera
sensor_size_mm = 4.8  # Sensor size in mm (for 1/2.55" sensor)
focal_length_mm = 4.15  # Focal length in mm
known_distance_cm = 28.0  # Known distance in cm (this is for calibration)

def process_iphone_depth(depth_image_path):
    """Process iPhone depth map with correct byte swapping"""
    depth_data = cv2.imread(depth_image_path, cv2.IMREAD_UNCHANGED)
    if depth_data is None:
        raise ValueError("Could not read depth image")
    
    # If the image has 4 channels (RGBA), convert to grayscale
    if depth_data.shape[2] == 4:
        depth_data = cv2.cvtColor(depth_data, cv2.COLOR_BGRA2GRAY)
    
    # Convert to uint16 and swap bytes using numpy's built-in method
    depth_data = depth_data.astype(np.uint16)
    depth_data = depth_data.byteswap()  # Correct endianness conversion
    
    # Convert mm to meters, handle invalid pixels
    depth_map = np.where(depth_data >= 65535, np.nan, depth_data.astype(np.float32) / 1000.0)
    return depth_map

def on_click(event):
    global roi_coords, click_count
    if event.inaxes != plt.gca():
        return
    
    if click_count == 0:
        roi_coords = [(int(event.xdata), int(event.ydata))]
        click_count = 1
        print("Click the opposite corner to complete the rectangle")
    elif click_count == 1:
        roi_coords.append((int(event.xdata), int(event.ydata)))
        click_count = 0
        plt.close()

def estimate_object_dimensions(depth_image_path, known_distance_cm):
    global roi_coords
    
    # Process depth data
    depth_map = process_iphone_depth(depth_image_path)
    
    # Create normalized display image
    valid_depth = np.nan_to_num(depth_map, nan=0.0)
    display_image = cv2.normalize(valid_depth, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    
    # First click: show original depth image
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(display_image, cmap='gray')
    ax.set_title("Click two points to define object boundaries")
    fig.canvas.mpl_connect('button_press_event', on_click)
    plt.show()
    
    # Get coordinates
    (x1, y1), (x2, y2) = roi_coords
    x1, x2 = sorted([x1, x2])
    y1, y2 = sorted([y1, y2])
    
    # Get ROI data
    roi = depth_map[y1:y2, x1:x2]
    
    # Debug output
    print(f"\nROI Pixel Range: {x1}-{x2} (width: {x2-x1}px), {y1}-{y2} (height: {y2-y1}px)")
    print(f"Raw depth values (mm): {roi * 1000}")
    
    # Calculate median depth
    median_depth_cm = np.nanmedian(roi) * 100
    print(f"Calculated median depth: {median_depth_cm:.1f} cm")
    
    # Verify depth validity
    if abs(median_depth_cm - known_distance_cm) > 10:
        print(f"⚠️ Warning: Large depth discrepancy ({median_depth_cm:.1f} cm vs reference {known_distance_cm} cm)")

    # Improved scaling: account for iPhone 14 Plus's focal length and sensor size
    # Using the camera model formula: Real-world size = (Object size in pixels) * (Distance to object) / Focal length
    pixel_size_mm = sensor_size_mm / 12  # Assuming a 12 MP camera, 1 micron per pixel
    scale_factor = (known_distance_cm * 10) / (median_depth_cm * focal_length_mm)  # Convert to cm scale

    # Calculate dimensions
    width_cm = (x2 - x1) * scale_factor
    height_cm = (y2 - y1) * scale_factor
    
    # Debug output for scaling
    print(f"Scale factor: {scale_factor:.2f}")
    print(f"Estimated width: {width_cm:.1f} cm, height: {height_cm:.1f} cm")
    
    # Show results
    result_img = cv2.cvtColor(display_image, cv2.COLOR_GRAY2RGB)
    cv2.rectangle(result_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(result_img)
    ax.set_title(f"Width: {width_cm:.1f} cm | Height: {height_cm:.1f} cm")
    plt.axis('off')
    plt.show()
    
    return width_cm, height_cm

if __name__ == "__main__":
    estimate_object_dimensions(
        depth_image_path=r"C:\Users\USER\Downloads\inverse_depth_map (2).png",
        known_distance_cm=30
    )
