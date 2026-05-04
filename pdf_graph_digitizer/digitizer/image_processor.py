import cv2
import numpy as np

def extract_curve_pixels(image, target_color_bgr, bounding_box=None):
    """Isolates a curve based on color and an optional bounding box."""
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    color_hsv = cv2.cvtColor(np.uint8([[target_color_bgr]]), cv2.COLOR_BGR2HSV)[0][0]
    
    # Cast to python int to prevent numpy uint8 overflow during addition
    h_val = int(color_hsv[0])
    s_val = int(color_hsv[1])
    v_val = int(color_hsv[2])
    
    # Tolerances for detecting the specified color
    h_tol, s_tol, v_tol = 15, 60, 60
    
    if s_val < 30:
        # Grayscale colors (black, gray, white) have meaningless hue.
        # Ignore hue entirely and just match on Value (lightness) and low Saturation.
        lower = np.array([0, 0, max(0, v_val - v_tol - 20)])
        upper = np.array([179, s_val + s_tol, min(255, v_val + v_tol + 20)])
        mask = cv2.inRange(hsv_image, lower, upper)
    elif h_val < h_tol:
        # Handle Hue wrap-around for red colors
        lower1 = np.array([0, max(0, s_val - s_tol), max(0, v_val - v_tol)])
        upper1 = np.array([h_val + h_tol, min(255, s_val + s_tol), min(255, v_val + v_tol)])
        lower2 = np.array([180 - (h_tol - h_val), max(0, s_val - s_tol), max(0, v_val - v_tol)])
        upper2 = np.array([179, min(255, s_val + s_tol), min(255, v_val + v_tol)])
        mask1 = cv2.inRange(hsv_image, lower1, upper1)
        mask2 = cv2.inRange(hsv_image, lower2, upper2)
        mask = cv2.bitwise_or(mask1, mask2)
    elif h_val > 179 - h_tol:
        lower1 = np.array([h_val - h_tol, max(0, s_val - s_tol), max(0, v_val - v_tol)])
        upper1 = np.array([179, min(255, s_val + s_tol), min(255, v_val + v_tol)])
        lower2 = np.array([0, max(0, s_val - s_tol), max(0, v_val - v_tol)])
        upper2 = np.array([(h_val + h_tol) - 180, min(255, s_val + s_tol), min(255, v_val + v_tol)])
        mask1 = cv2.inRange(hsv_image, lower1, upper1)
        mask2 = cv2.inRange(hsv_image, lower2, upper2)
        mask = cv2.bitwise_or(mask1, mask2)
    else:
        lower = np.array([h_val - h_tol, max(0, s_val - s_tol), max(0, v_val - v_tol)])
        upper = np.array([h_val + h_tol, min(255, s_val + s_tol), min(255, v_val + v_tol)])
        mask = cv2.inRange(hsv_image, lower, upper)
    
    # Minimal morphological noise removal that won't destroy thin lines
    # Only dilate to connect slightly broken lines, then close
    kernel = np.ones((2, 2), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    if bounding_box:
        x_min, x_max, y_min, y_max = [int(v) for v in bounding_box]
        mask[:, :max(0, x_min)] = 0
        mask[:, min(mask.shape[1], x_max):] = 0
        mask[:max(0, y_min), :] = 0
        mask[min(mask.shape[0], y_max):, :] = 0
        
    y_idx, x_idx = np.where(mask > 0)
    
    if len(x_idx) == 0:
        return [], []
        
    unique_x = np.unique(x_idx)
    curve_px_x = []
    curve_px_y = []
    
    # Calculate median Y for each X point to get a single-valued function
    for ux in unique_x:
        uy = np.median(y_idx[x_idx == ux])
        curve_px_x.append(ux)
        curve_px_y.append(uy)
        
    return curve_px_x, curve_px_y
