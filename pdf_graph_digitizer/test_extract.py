import cv2
import numpy as np
from digitizer.image_processor import extract_curve_pixels

img = np.zeros((100, 100, 3), dtype=np.uint8)
# draw a blue line
cv2.line(img, (10, 50), (90, 50), (255, 0, 0), 1)

target_color = img[50, 50] # (255, 0, 0)
print("Target color:", target_color)

px, py = extract_curve_pixels(img, target_color)
print(f"Found {len(px)} pixels")
