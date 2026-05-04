import fitz
import numpy as np
import cv2

def load_pdf_images(pdf_path):
    """Loads a PDF and extracts pages as high-resolution images (300 DPI)."""
    doc = fitz.open(pdf_path)
    images = []
    for i in range(len(doc)):
        page = doc[i]
        pix = page.get_pixmap(dpi=300)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        images.append((f"Page {i+1}", img))
    return images
