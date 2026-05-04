import numpy as np
from scipy.signal import savgol_filter
import cv2
from .image_processor import extract_curve_pixels

class CurveExtractor:
    """Manages extraction and smoothing of multiple curves."""
    def __init__(self, calibrator):
        self.calibrator = calibrator
        self.curves = {}

    def extract_curve(self, name, image, px, py, y_axis_name, x_axis_name='X'):
        # Improve color picking by searching a small neighborhood
        h, w = image.shape[:2]
        r = 3
        y1, y2 = max(0, py - r), min(h, py + r + 1)
        x1, x2 = max(0, px - r), min(w, px + r + 1)
        patch = image[y1:y2, x1:x2]
        
        # Find the pixel in the patch with the highest saturation
        hsv_patch = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
        s_channel = hsv_patch[:,:,1]
        
        if np.max(s_channel) > 30:
            # Pick the pixel with max saturation to avoid white/gray anti-aliased edges
            max_y, max_x = np.unravel_index(np.argmax(s_channel), s_channel.shape)
            target_color_bgr = patch[max_y, max_x]
        else:
            # If everything is low saturation (grayscale), pick darkest pixel
            v_channel = hsv_patch[:,:,2]
            min_y, min_x = np.unravel_index(np.argmin(v_channel), v_channel.shape)
            target_color_bgr = patch[min_y, min_x]
        
        # Do not enforce a strict bounding box based on calibration points.
        # This allows curves that extend beyond the calibrated interval to be fully extracted.
        px_x, px_y = extract_curve_pixels(image, target_color_bgr)
        
        if not px_x:
            raise ValueError("No pixels found. Please ensure you click precisely on the curve line.")
            
        real_x = self.calibrator.apply(px_x, x_axis_name)
        real_y = self.calibrator.apply(px_y, y_axis_name)
        
        sort_idx = np.argsort(real_x)
        real_x = np.array(real_x)[sort_idx]
        real_y = np.array(real_y)[sort_idx]
        
        # Dynamic smoothing
        if len(real_x) > 15:
            window = min(len(real_x) // 10, 51)
            if window % 2 == 0: window += 1
            if window > 3:
                real_y = savgol_filter(real_y, window, 3)
                
        self.curves[name] = {'x': real_x, 'y': real_y, 'y_axis': y_axis_name}
        return self.curves[name]
