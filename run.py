#!/usr/bin/env python3
"""
Simple startup script for the Document OCR Converter
"""

import uvicorn
import sys
import os
from pathlib import Path

def main():
    """Start the FastAPI application"""
    
    # Create necessary directories if they don't exist
    directories = ['uploads', 'outputs', 'templates', 'static']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # Check if Tesseract is available
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("✅ Tesseract OCR is available")
    except Exception as e:
        print("❌ Tesseract OCR not found. Please install Tesseract OCR.")
        print("   See README.md for installation instructions.")
        print(f"   Error: {e}")
        sys.exit(1)
    
    # Start the server
    print("🚀 Starting Document OCR Converter...")
    print("📱 Web interface: http://localhost:8000")
    print("📚 API docs: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
