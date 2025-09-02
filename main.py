from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
import logging

from ocr_processor import OCRProcessor
from file_converter import FileConverter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Document OCR Converter", version="1.0.0")

# Create necessary directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize processors
ocr_processor = OCRProcessor()
file_converter = FileConverter()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main upload page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    output_format: str = Form(...)
):
    """
    Upload and process a document file
    """
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} not supported. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Validate output format
        allowed_formats = ['json', 'csv', 'txt']
        if output_format not in allowed_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Output format {output_format} not supported. Allowed formats: {', '.join(allowed_formats)}"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        input_filename = f"{file_id}{file_extension}"
        input_path = UPLOAD_DIR / input_filename
        
        # Save uploaded file
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File uploaded: {input_filename}")
        
        # Process the file with OCR
        extracted_text = await ocr_processor.process_file(input_path)
        
        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from the document. Please ensure the document contains readable text."
            )
        
        # Convert to requested format
        output_filename = f"{file_id}.{output_format}"
        output_path = OUTPUT_DIR / output_filename

        logger.info(f"Converting to {output_format} format...")
        logger.info(f"Output path: {output_path}")
        logger.info(f"Extracted text length: {len(extracted_text)}")

        # If CSV requested, first persist TXT then build CSV from that TXT for robustness
        if output_format == 'csv':
            # 1) Write TXT
            txt_path = OUTPUT_DIR / f"{file_id}.txt"
            await file_converter._convert_to_txt(extracted_text, txt_path)
            # 2) Read TXT back
            with open(txt_path, 'r', encoding='utf-8') as f:
                txt_content = f.read()
            # 3) Generate CSV synchronously from TXT content
            file_converter._convert_to_csv_sync(txt_content, output_path)
        else:
            await file_converter.convert_to_format(extracted_text, output_path, output_format)
        
        # Verify the output file was created
        if output_path.exists():
            file_size = output_path.stat().st_size
            logger.info(f"Output file created successfully: {output_filename} ({file_size} bytes)")
        else:
            logger.error(f"Output file was not created: {output_path}")
        
        logger.info(f"File processed successfully: {output_filename}")
        
        # Clean up input file
        input_path.unlink()
        
        return {
            "message": "File processed successfully",
            "file_id": file_id,
            "output_format": output_format,
            "download_url": f"/download/{output_filename}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download the converted file
    """
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "OCR Converter API is running"}

@app.get("/test-csv")
async def test_csv_conversion():
    """Test CSV conversion with sample text"""
    try:
        test_text = "This is a test document.\n\nIt has multiple paragraphs.\n\nEach paragraph contains several sentences."
        
        # Create test file
        test_file_id = str(uuid.uuid4())
        test_output_path = OUTPUT_DIR / f"{test_file_id}.csv"
        
        logger.info(f"Testing CSV conversion with text: {test_text}")
        
        # Test CSV conversion directly
        file_converter._convert_to_csv_sync(test_text, test_output_path)
        
        if test_output_path.exists():
            file_size = test_output_path.stat().st_size
            with open(test_output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean up test file
            test_output_path.unlink()
            
            return {
                "status": "success",
                "file_size": file_size,
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            }
        else:
            return {"status": "error", "message": "CSV file was not created"}
            
    except Exception as e:
        logger.error(f"Test CSV conversion failed: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
