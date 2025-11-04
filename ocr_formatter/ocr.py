import cv2
import numpy as np
import pytesseract
from PIL import Image

from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class OCRProcessor:
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize the OCR processor.
        
        Args:
            tesseract_cmd: Optional path to tesseract executable
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    def process_image(self, image_path: str, save_debug: bool = True) -> str:
        """
        Extract text from an image using OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            str: Extracted text from the image
        """
        try:
            # Open the image
            with Image.open(image_path) as img:
                # 1. Read in grayscale
                img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    raise ValueError(f"Could not read image: {image_path}")

                # 2. Gentle denoising
                img = cv2.fastNlMeansDenoising(img, h=8, templateWindowSize=7, searchWindowSize=21)

                # 3. Background normalization to correct uneven lighting
                background = cv2.medianBlur(img, 25)
                normalized = cv2.divide(img, background, scale=255)

                # 4. Local contrast enhancement using CLAHE (Contrast Limited Adaptive Histogram Equalization)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(normalized)

                # 5. Global binarization using Otsu
                _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                # 6. Slight dilation to connect broken strokes
                kernel = np.ones((1, 1), np.uint8)
                binary = cv2.dilate(binary, kernel, iterations=1)

                # 7. Unsharp masking (sharpen strokes)
                blur = cv2.GaussianBlur(binary, (3, 3), 0)
                sharpened = cv2.addWeighted(binary, 1.5, blur, -0.5, 0)

                # 8. Invert if needed (Tesseract expects black text on white)
                if np.mean(sharpened) < 127:
                    sharpened = cv2.bitwise_not(sharpened)

                # 9. Resize for better OCR accuracy
                sharpened = cv2.resize(sharpened, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

                # Save for debugging
                if save_debug:
                    cv2.imwrite("preprocessed.png", sharpened)

                # Convert to PIL Image for pytesseract
                pil_img = Image.fromarray(sharpened)
                
                # Extract text using pytesseract
                text = pytesseract.image_to_string(pil_img)
                print(f"Text extracted by OCR: {text}")
                
                return text.strip()
                
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            raise
