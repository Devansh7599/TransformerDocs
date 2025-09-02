import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import logging
from pathlib import Path
from typing import List, Optional
import asyncio
import aiofiles

logger = logging.getLogger(__name__)

class OCRProcessor:
    """
    Handles OCR processing for various document types
    """
    
    def __init__(self):
        # Configure Tesseract (you may need to adjust this path based on your system)
        # For Windows, you might need to set the path to tesseract.exe
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
    
    async def process_file(self, file_path: Path) -> str:
        """
        Process a file and extract text using OCR
        """
        file_extension = file_path.suffix.lower()
        
        if file_extension == '.pdf':
            return await self._process_pdf(file_path)
        elif file_extension in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            return await self._process_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    async def _process_pdf(self, pdf_path: Path) -> str:
        """
        Process PDF file by converting to images and then applying OCR
        """
        try:
            logger.info(f"Processing PDF: {pdf_path}")
            
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)
            
            if not images:
                raise ValueError("No pages found in PDF")
            
            extracted_texts = []
            
            for i, image in enumerate(images):
                logger.info(f"Processing page {i + 1} of {len(images)}")
                
                # Apply OCR to each page
                page_text = await self._extract_text_from_image(image)
                if page_text.strip():
                    extracted_texts.append(f"--- Page {i + 1} ---\n{page_text}")
            
            return "\n\n".join(extracted_texts)
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            raise
    
    async def _process_image(self, image_path: Path) -> str:
        """
        Process image file and extract text using OCR
        """
        try:
            logger.info(f"Processing image: {image_path}")
            
            # Open and process the image
            with Image.open(image_path) as image:
                # Convert to RGB if necessary
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                return await self._extract_text_from_image(image)
                
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            raise
    
    async def _extract_text_from_image(self, image: Image.Image) -> str:
        """
        Extract text from PIL Image using Tesseract OCR
        """
        try:
            # Run OCR in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                None, 
                self._run_tesseract_ocr, 
                image
            )
            return text
            
        except Exception as e:
            logger.error(f"Error in OCR extraction: {str(e)}")
            raise
    
    def _run_tesseract_ocr(self, image: Image.Image) -> str:
        """
        Run Tesseract OCR on the image
        """
        try:
            # Configure Tesseract for better accuracy
            custom_config = r'--oem 3 --psm 6'
            
            # Extract text
            text = pytesseract.image_to_string(image, config=custom_config)
            
            # Clean up the text
            text = self._clean_text(text)
            
            return text
            
        except Exception as e:
            logger.error(f"Tesseract OCR error: {str(e)}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and format the extracted text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove leading/trailing whitespace
            line = line.strip()
            
            # Skip empty lines
            if line:
                cleaned_lines.append(line)
        
        # Join lines with single newlines
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove multiple consecutive newlines
        while '\n\n\n' in cleaned_text:
            cleaned_text = cleaned_text.replace('\n\n\n', '\n\n')
        
        return cleaned_text
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported file formats
        """
        return ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
