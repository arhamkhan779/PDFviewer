import fitz  # PyMuPDF
import pytesseract
import os
import io
from concurrent.futures import ThreadPoolExecutor
from logger import logging
from PIL import Image

'''
A Python Package For Optical Character Recognition
'''

class PdfToText:
    '''
    Class: To Extract Text from PDFs
    Tools: Tesseract, PyMuPDF, Pillow
    Methodology: Modular Architecture
    '''

    def __init__(self, tesseract_path: str) -> None:
        self.tesseract_cmd = tesseract_path
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd  # Set Tesseract path

    def preprocess_image(self, img: Image.Image) -> Image.Image:
        """Preprocess image for better OCR accuracy."""
        try:
            gray = img.convert('L')  # Convert to grayscale
            thresh = gray.point(lambda p: 0 if p < 200 else 255)  # Apply thresholding
            return thresh
        except Exception as e:
            logging.info(f"Exception Encountered: {e}")

    def ocr_img(self, img: Image.Image) -> str:
        """Extract text from a single image."""
        try:
            img = self.preprocess_image(img)  # Apply preprocessing
            text = pytesseract.image_to_string(img, config="--psm 6")  # Optimize OCR mode
            return text
        except Exception as e:
            logging.info(f"Exception Encountered: {e}")
            return ""

    def process_page(self, page) -> str:
        """Convert a single PDF page to an image and extract text."""
        try:
            pix = page.get_pixmap(dpi=300)  # Convert page to image with high DPI
            img = Image.open(io.BytesIO(pix.tobytes("png")))  # Convert to PIL Image
            return self.ocr_img(img)  # Extract text
        except Exception as e:
            logging.info(f"Exception Encountered: {e}")
            return ""

    def pdf_to_text(self, pdf_path: str) -> str:
        """Convert PDF to images and extract text from all pages in parallel."""
        try:
            doc = fitz.open(pdf_path)  # Open PDF
            text_output = []
            with ThreadPoolExecutor() as executor:
                results = executor.map(self.process_page, doc)  # Run OCR in parallel
                text_output.extend(results)
            return "\n".join(text_output)
        except Exception as e:
            logging.info(f"Exception Encountered: {e}")
            return ""
