from PIL import Image
import pytesseract
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
    
    def process_image(self, image_path: str) -> str:
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
                # Convert image to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Extract text using pytesseract
                text = pytesseract.image_to_string(img)
                
                return text.strip()
                
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            raise
    
    def process_multiple_images(self, image_paths: List[str]) -> str:
        """
        Process multiple images and combine their text.
        
        Args:
            image_paths: List of paths to image files
            
        Returns:
            str: Combined extracted text from all images
        """
        texts = []
        for image_path in image_paths:
            text = self.process_image(image_path)
            texts.append(text)
        
        return "\n\n".join(texts)