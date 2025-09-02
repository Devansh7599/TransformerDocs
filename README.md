# Document OCR Converter

A FastAPI-based web application that converts non-machine readable documents (PDF, images) to machine-readable formats (JSON, CSV, TXT) using Optical Character Recognition (OCR).

## Features

- **Multi-format Input Support**: PDF, PNG, JPG, JPEG, TIFF, BMP
- **Multiple Output Formats**: JSON, CSV, TXT
- **High-Quality OCR**: Uses Tesseract OCR with optimized settings
- **Web Interface**: Beautiful, responsive web UI for easy file upload
- **RESTful API**: Programmatic access via API endpoints
- **Async Processing**: Non-blocking file processing for better performance
- **Error Handling**: Comprehensive error handling and validation

## Prerequisites

### System Requirements

1. **Python 3.8+**
2. **Tesseract OCR Engine**

#### Installing Tesseract OCR

**Windows:**
1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install the executable
3. Add Tesseract to your system PATH, or uncomment and modify the path in `ocr_processor.py`:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

**Linux (CentOS/RHEL):**
```bash
sudo yum install tesseract
```

## Installation

1. **Clone or download the project files**

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create necessary directories:**
   ```bash
   mkdir uploads outputs templates static
   ```

## Usage

### Running the Application

1. **Start the FastAPI server:**
   ```bash
   python main.py
   ```
   
       Or using uvicorn directly:
    ```bash
    uvicorn main:app --host 127.0.0.1 --port 8000 --reload
    ```

2. **Open your web browser and navigate to:**
   ```
   http://localhost:8000
   ```

### Web Interface

1. **Upload a document**: Click the upload area or drag and drop a file
2. **Select output format**: Choose from JSON, CSV, or TXT
3. **Click "Convert Document"**: Wait for processing to complete
4. **Download the result**: Click the download button when ready

### API Endpoints

#### Upload and Convert Document
```http
POST /upload
Content-Type: multipart/form-data

Parameters:
- file: Document file (PDF, PNG, JPG, JPEG, TIFF, BMP)
- output_format: Output format (json, csv, txt)
```

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/upload" \
     -F "file=@document.pdf" \
     -F "output_format=json"
```

**Response:**
```json
{
  "message": "File processed successfully",
  "file_id": "uuid-string",
  "output_format": "json",
  "download_url": "/download/uuid-string.json"
}
```

#### Download Converted File
```http
GET /download/{filename}
```

#### Health Check
```http
GET /health
```

## Output Formats

### JSON Format
Structured data containing:
- Document metadata (page count, word count, etc.)
- Full extracted text
- Paragraphs and sentences arrays
- Processing metadata

### CSV Format
Spreadsheet-compatible format with:
- Document summary statistics
- Paragraphs in separate rows
- Sentences in separate rows
- Full text content

### TXT Format
Clean, formatted plain text with:
- Document statistics header
- Properly formatted content
- Page separators (for multi-page documents)

## Project Structure

```
document-ocr-converter/
├── main.py                 # FastAPI application
├── ocr_processor.py        # OCR processing logic
├── file_converter.py       # Format conversion logic
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── templates/
│   └── index.html         # Web interface
├── static/                # Static files (CSS, JS)
├── uploads/               # Temporary upload directory
└── outputs/               # Converted files directory
```

## Configuration

### OCR Settings
The OCR processor uses optimized settings for better accuracy:
- **OEM Mode 3**: Default OCR Engine Mode
- **PSM Mode 6**: Uniform block of text
- **DPI 300**: High resolution for PDF conversion

### File Size Limits
- Default FastAPI file upload limit applies
- For large files, consider increasing the limit in your deployment

## Troubleshooting

### Common Issues

1. **"Tesseract not found" error:**
   - Ensure Tesseract is installed and in your PATH
   - Or set the correct path in `ocr_processor.py`

2. **"No text could be extracted" error:**
   - Check if the document contains readable text
   - Try with a higher quality image/PDF
   - Ensure the document is not password-protected

3. **Poor OCR accuracy:**
   - Use higher resolution images (300+ DPI)
   - Ensure good contrast between text and background
   - Try different image formats

4. **Memory issues with large PDFs:**
   - Process smaller batches of pages
   - Increase system memory or use a more powerful server

### Performance Tips

- Use PNG or TIFF formats for better OCR accuracy
- Ensure images are at least 300 DPI
- For large documents, consider splitting into smaller files
- Use SSD storage for better I/O performance

## Development

### Adding New Output Formats

1. Add the format to `FileConverter.get_supported_formats()`
2. Implement a new `_convert_to_[format]()` method
3. Update the web interface to include the new format

### Adding New Input Formats

1. Add the format to `OCRProcessor.get_supported_formats()`
2. Implement processing logic in `process_file()` method
3. Update the web interface file input accept attribute

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the FastAPI and Tesseract documentation
3. Open an issue in the project repository
