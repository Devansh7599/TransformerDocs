#!/usr/bin/env python3
"""
Simple test script to verify the application components work correctly
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import pytesseract
        print("✅ Pytesseract imported successfully")
    except ImportError as e:
        print(f"❌ Pytesseract import failed: {e}")
        return False
    
    try:
        from PIL import Image
        print("✅ Pillow imported successfully")
    except ImportError as e:
        print(f"❌ Pillow import failed: {e}")
        return False
    
    try:
        import pdf2image
        print("✅ pdf2image imported successfully")
    except ImportError as e:
        print(f"❌ pdf2image import failed: {e}")
        return False
    
    try:
        import pandas
        print("✅ Pandas imported successfully")
    except ImportError as e:
        print(f"❌ Pandas import failed: {e}")
        return False
    
    return True

def test_tesseract():
    """Test if Tesseract OCR is available"""
    print("\nTesting Tesseract OCR...")
    
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract OCR version: {version}")
        return True
    except Exception as e:
        print(f"❌ Tesseract OCR not available: {e}")
        print("   Please install Tesseract OCR. See README.md for instructions.")
        return False

def test_application_modules():
    """Test if our application modules can be imported"""
    print("\nTesting application modules...")
    
    try:
        from ocr_processor import OCRProcessor
        ocr = OCRProcessor()
        print("✅ OCRProcessor imported and instantiated")
    except Exception as e:
        print(f"❌ OCRProcessor failed: {e}")
        return False
    
    try:
        from file_converter import FileConverter
        converter = FileConverter()
        print("✅ FileConverter imported and instantiated")
    except Exception as e:
        print(f"❌ FileConverter failed: {e}")
        return False
    
    try:
        import main
        print("✅ Main application module imported")
    except Exception as e:
        print(f"❌ Main application failed: {e}")
        return False
    
    return True

def test_directories():
    """Test if required directories exist or can be created"""
    print("\nTesting directories...")
    
    directories = ['uploads', 'outputs', 'templates', 'static']
    
    for directory in directories:
        try:
            Path(directory).mkdir(exist_ok=True)
            if Path(directory).exists():
                print(f"✅ Directory '{directory}' exists")
            else:
                print(f"❌ Directory '{directory}' could not be created")
                return False
        except Exception as e:
            print(f"❌ Error with directory '{directory}': {e}")
            return False
    
    return True

def main():
    """Run all tests"""
    print("🧪 Testing Document OCR Converter Setup")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_tesseract,
        test_application_modules,
        test_directories
    ]
    
    all_passed = True
    
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! The application should work correctly.")
        print("\nTo start the application, run:")
        print("  python run.py")
        print("  or")
        print("  start.bat (on Windows)")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("   Make sure all dependencies are installed correctly.")
        sys.exit(1)

if __name__ == "__main__":
    main()
