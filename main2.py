import cv2
import numpy as np

# Global variables
polygon_points = []
ruler_points = []
current_mode = 'polygon'
img = None
img_copy = None
display_img = None  # For resized display
scale_factor = 1.0  # To calculate back the original dimensions

def mouse_event(event, x, y, flags, param):
    global polygon_points, ruler_points, current_mode, img, img_copy, display_img, scale_factor
    if event == cv2.EVENT_LBUTTONDOWN:
        # Scale coordinates back to the original image size
        x_original = int(x / scale_factor)
        y_original = int(y / scale_factor)

        if current_mode == 'polygon':
            polygon_points.append((x_original, y_original))
            cv2.circle(display_img, (x, y), 3, (0, 0, 255), -1)
            if len(polygon_points) > 1:
                pt1 = (int(polygon_points[-2][0] * scale_factor), int(polygon_points[-2][1] * scale_factor))
                pt2 = (int(polygon_points[-1][0] * scale_factor), int(polygon_points[-1][1] * scale_factor))
                cv2.line(display_img, pt1, pt2, (0, 255, 0), 1)
            cv2.imshow('image', display_img)
        elif current_mode == 'ruler' and len(ruler_points) < 2:
            ruler_points.append((x_original, y_original))
            cv2.circle(display_img, (x, y), 3, (255, 0, 0), -1)
            if len(ruler_points) == 2:
                pt1 = (int(ruler_points[0][0] * scale_factor), int(ruler_points[0][1] * scale_factor))
                pt2 = (int(ruler_points[1][0] * scale_factor), int(ruler_points[1][1] * scale_factor))
                cv2.line(display_img, pt1, pt2, (255, 0, 0), 2)
            cv2.imshow('image', display_img)

def resize_image(image, max_width=800, max_height=600):
    h, w = image.shape[:2]
    scale = min(max_width / w, max_height / h, 1.0)  # Scale down if needed
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, scale

def main():
    global img, img_copy, display_img, current_mode, scale_factor
    img_path = input("Enter image path: ")
    img = cv2.imread(img_path)
    if img is None:
        print("Error loading image")
        return

    img_copy = img.copy()

    # Resize the image for display
    display_img, scale_factor = resize_image(img)
    cv2.namedWindow('image')
    cv2.setMouseCallback('image', mouse_event)

    print("Instructions:")
    print("1. Left-click to draw polygon points on the apple")
    print("2. Press ENTER to finish polygon")
    print("3. Left-click two points on the ruler")
    print("4. Press 'q' to quit anytime")

    # Polygon drawing stage
    while True:
        cv2.imshow('image', display_img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cv2.destroyAllWindows()
            return
        elif key == 13:  # Enter key
            if len(polygon_points) >= 3:
                pt1 = (int(polygon_points[-1][0] * scale_factor), int(polygon_points[-1][1] * scale_factor))
                pt2 = (int(polygon_points[0][0] * scale_factor), int(polygon_points[0][1] * scale_factor))
                cv2.line(display_img, pt1, pt2, (0, 255, 0), 1)
                current_mode = 'ruler'
                cv2.imshow('image', display_img)
                break

    # Ruler drawing stage
    while True:
        cv2.imshow('image', display_img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cv2.destroyAllWindows()
            return
        if len(ruler_points) >= 2:
            break

    cv2.destroyAllWindows()

    # Measurement input
    ruler_length_cm = float(input("Enter ruler line length (cm): "))

    # Calculate scale
    pt1 = np.array(ruler_points[0])
    pt2 = np.array(ruler_points[1])
    ruler_length_px = np.linalg.norm(pt1 - pt2)
    px_per_cm = ruler_length_px / ruler_length_cm

    # Calculate polygon area
    contour = np.array(polygon_points, dtype=np.int32)
    area_px = cv2.contourArea(contour)
    area_cm = area_px / (px_per_cm ** 2)

    # Calculate apple dimensions
    x = [p[0] for p in polygon_points]
    y = [p[1] for p in polygon_points]
    width_px = max(x) - min(x)
    height_px = max(y) - min(y)
    width_cm = width_px / px_per_cm
    height_cm = height_px / px_per_cm

    print("\nResults:")
    print(f"Apple width: {width_cm:.2f} cm")
    print(f"Apple height: {height_cm:.2f} cm")
    print(f"Polygon area: {area_cm:.2f} cm²")

if __name__ == "__main__":
    main()
