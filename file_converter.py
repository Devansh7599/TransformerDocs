import json
import csv
import re
import os
from pathlib import Path
from typing import Dict, List, Any
import logging
import asyncio
import aiofiles

logger = logging.getLogger(__name__)

class FileConverter:
    """
    Handles conversion of extracted text to various output formats
    """
    
    def __init__(self):
        try:
            # Increase CSV field size limit to handle very large OCR blocks
            csv.field_size_limit(1_000_000_000)
        except Exception:
            # Fallback to a high but safer value if platform caps it
            try:
                csv.field_size_limit(10_000_000)
            except Exception:
                pass
    
    async def convert_to_format(self, text: str, output_path: Path, format_type: str):
        """
        Convert extracted text to the specified format
        """
        try:
            logger.info(f"Starting conversion to {format_type} format")
            logger.info(f"Text length: {len(text)}")
            logger.info(f"Output path: {output_path}")
            
            if format_type == 'json':
                await self._convert_to_json(text, output_path)
            elif format_type == 'csv':
                # Persist raw TXT first next to the CSV, then build CSV from it
                txt_path = output_path.with_suffix('.txt')
                self._write_raw_txt(text, txt_path)
                with open(txt_path, 'r', encoding='utf-8') as f:
                    txt_content = f.read()
                # Use synchronous CSV conversion
                self._convert_to_csv_sync(txt_content, output_path)
            elif format_type == 'txt':
                await self._convert_to_txt(text, output_path)
            else:
                raise ValueError(f"Unsupported output format: {format_type}")
                
            logger.info(f"Successfully converted to {format_type}: {output_path}")
            
        except Exception as e:
            logger.error(f"Error converting to {format_type}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def _convert_to_json(self, text: str, output_path: Path):
        """
        Convert text to JSON format
        """
        try:
            # Parse the text into structured data
            structured_data = self._parse_text_to_structured_data(text)
            
            # Create JSON structure
            json_data = {
                "document_info": {
                    "total_pages": structured_data.get("page_count", 1),
                    "total_paragraphs": len(structured_data.get("paragraphs", [])),
                    "total_words": len(text.split()),
                    "total_characters": len(text)
                },
                "content": {
                    "full_text": text,
                    "paragraphs": structured_data.get("paragraphs", []),
                    "sentences": structured_data.get("sentences", []),
                    "words": structured_data.get("words", [])
                },
                "metadata": {
                    "extraction_method": "OCR",
                    "format": "json"
                }
            }
            
            # Write JSON file
            async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(json_data, indent=2, ensure_ascii=False))
                
        except Exception as e:
            logger.error(f"Error converting to JSON: {str(e)}")
            raise
    
    async def _convert_to_csv(self, text: str, output_path: Path):
        """
        Convert text to CSV format
        """
        try:
            logger.info(f"Starting CSV conversion for text length: {len(text)}")
            logger.info(f"Output path: {output_path}")
            logger.info(f"Output directory exists: {output_path.parent.exists()}")
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Parse text into structured data
            structured_data = self._parse_text_to_structured_data(text)
            logger.info(f"Parsed data: {len(structured_data.get('paragraphs', []))} paragraphs, {len(structured_data.get('sentences', []))} sentences")
            
            # Prepare CSV data
            csv_data = []
            
            # Add document summary
            csv_data.append(["Document Summary", ""])
            csv_data.append(["Total Pages", structured_data.get("page_count", 1)])
            csv_data.append(["Total Paragraphs", len(structured_data.get("paragraphs", []))])
            csv_data.append(["Total Words", len(text.split())])
            csv_data.append(["Total Characters", len(text)])
            csv_data.append(["", ""])  # Empty row
            
            # Add paragraphs
            csv_data.append(["Paragraphs", ""])
            for i, paragraph in enumerate(structured_data.get("paragraphs", []), 1):
                csv_data.append([f"Paragraph {i}", paragraph])
            csv_data.append(["", ""])  # Empty row
            
            # Add sentences
            csv_data.append(["Sentences", ""])
            for i, sentence in enumerate(structured_data.get("sentences", []), 1):
                csv_data.append([f"Sentence {i}", sentence])
            csv_data.append(["", ""])  # Empty row
            
            # Add full text
            csv_data.append(["Full Text", ""])
            csv_data.append(["Content", text])
            
            logger.info(f"Prepared {len(csv_data)} rows for CSV")
            
            # Write CSV file with explicit error handling
            try:
                # Use UTF-8 BOM for Excel, CRLF line endings, and quote all fields
                with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(
                        f,
                        dialect='excel',
                        quoting=csv.QUOTE_ALL,
                        lineterminator='\r\n'
                    )
                    writer.writerows(csv_data)
                    f.flush()  # Force write to disk
                    os.fsync(f.fileno())  # Ensure data is written to disk
                
                logger.info(f"CSV file written successfully to {output_path}")
                
                # Verify file was written
                if output_path.exists():
                    file_size = output_path.stat().st_size
                    logger.info(f"CSV file size: {file_size} bytes")
                    
                    # Read back first few lines to verify content
                    with open(output_path, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        logger.info(f"First line of CSV: {first_line}")
                else:
                    logger.error("CSV file was not created!")
                    
            except Exception as write_error:
                logger.error(f"Error writing CSV file: {write_error}")
                # Try alternative approach - write as string (with BOM and CRLF)
                csv_string = ''
                for row in csv_data:
                    escaped_cells = [str(cell).replace('"', '""') for cell in row]
                    csv_string += '"' + '","'.join(escaped_cells) + '"' + "\r\n"

                with open(output_path, 'w', encoding='utf-8-sig') as f:
                    f.write(csv_string)
                    f.flush()
                    os.fsync(f.fileno())
                
                logger.info(f"CSV written using alternative method")
                
        except Exception as e:
            logger.error(f"Error converting to CSV: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _convert_to_csv_sync(self, text: str, output_path: Path):
        """
        Synchronous CSV conversion to avoid async issues
        """
        try:
            logger.info(f"Starting synchronous CSV conversion for text length: {len(text)}")
            logger.info(f"Output path: {output_path}")
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Always build a line-based CSV to guarantee content
            lines = text.splitlines()
            csv_data = [["Line Number", "Line Text"]]
            for idx, line in enumerate(lines, 1):
                csv_data.append([idx, line])
            if len(lines) == 0:
                # As an ultimate fallback, write full text as a single cell
                csv_data.append([1, text])
            logger.info(f"Line-based CSV rows: {len(csv_data)}")
            
            # Write CSV file (Excel-friendly)
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(
                    f,
                    dialect='excel',
                    quoting=csv.QUOTE_ALL,
                    lineterminator='\r\n'
                )
                writer.writerows(csv_data)
                f.flush()
                os.fsync(f.fileno())
            
            # If file unexpectedly empty, rewrite as plain CSV string
            if output_path.exists() and output_path.stat().st_size == 0:
                logger.warning("CSV appears empty after writer; rewriting as plain string")
                csv_string = ''
                for row in csv_data:
                    escaped_cells = [str(cell).replace('"', '""') for cell in row]
                    csv_string += '"' + '","'.join(escaped_cells) + '"' + "\r\n"
                with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                    f.write(csv_string)
                    f.flush()
                    os.fsync(f.fileno())
            
            logger.info(f"CSV file written successfully to {output_path}")
            
            # Verify file was written
            if output_path.exists():
                file_size = output_path.stat().st_size
                logger.info(f"CSV file size: {file_size} bytes")
                
                # Read back first few lines to verify content
                with open(output_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    logger.info(f"First line of CSV: {first_line}")
            else:
                logger.error("CSV file was not created!")
                
        except Exception as e:
            logger.error(f"Error in synchronous CSV conversion: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _write_raw_txt(self, text: str, output_path: Path) -> None:
        """
        Write raw extracted text to TXT (no headers/formatting) to mirror the requested pipeline.
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception as e:
            logger.error(f"Error writing raw TXT before CSV: {e}")
            raise
    
    async def _convert_to_txt(self, text: str, output_path: Path):
        """
        Convert text to TXT format (cleaned and formatted)
        """
        try:
            # Clean and format the text
            formatted_text = self._format_text_for_txt(text)
            
            # Write TXT file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_text)
                
        except Exception as e:
            logger.error(f"Error converting to TXT: {str(e)}")
            raise
    
    def _parse_text_to_structured_data(self, text: str) -> Dict[str, Any]:
        """
        Parse text into structured data for JSON/CSV output
        """
        try:
            # Normalize newlines to Unix-style for consistent splitting
            if "\r\n" in text:
                text = text.replace("\r\n", "\n")
            elif "\r" in text:
                text = text.replace("\r", "\n")
            
            # Split into paragraphs
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            
            # Split into sentences
            sentences = []
            for paragraph in paragraphs:
                # Simple sentence splitting (can be improved with NLP libraries)
                para_sentences = re.split(r'[.!?]+', paragraph)
                sentences.extend([s.strip() for s in para_sentences if s.strip()])
            
            # Extract words
            words = text.split()
            
            # Count pages (based on page markers)
            page_count = text.count('--- Page') + 1 if '--- Page' in text else 1
            
            return {
                "paragraphs": paragraphs,
                "sentences": sentences,
                "words": words,
                "page_count": page_count
            }
            
        except Exception as e:
            logger.error(f"Error parsing text: {str(e)}")
            return {
                "paragraphs": [text],
                "sentences": [text],
                "words": text.split(),
                "page_count": 1
            }
    
    def _format_text_for_txt(self, text: str) -> str:
        """
        Format text for TXT output with proper structure
        """
        try:
            # Add header
            formatted_text = "=" * 50 + "\n"
            formatted_text += "EXTRACTED DOCUMENT TEXT\n"
            formatted_text += "=" * 50 + "\n\n"
            
            # Add document info
            words = text.split()
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            
            formatted_text += f"Document Statistics:\n"
            formatted_text += f"- Total Words: {len(words)}\n"
            formatted_text += f"- Total Paragraphs: {len(paragraphs)}\n"
            formatted_text += f"- Total Characters: {len(text)}\n\n"
            
            formatted_text += "-" * 50 + "\n"
            formatted_text += "DOCUMENT CONTENT\n"
            formatted_text += "-" * 50 + "\n\n"
            
            # Add the actual content
            formatted_text += text
            
            # Add footer
            formatted_text += "\n\n" + "=" * 50 + "\n"
            formatted_text += "End of Document\n"
            formatted_text += "=" * 50 + "\n"
            
            return formatted_text
            
        except Exception as e:
            logger.error(f"Error formatting text: {str(e)}")
            return text
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported output formats
        """
        return ['json', 'csv', 'txt']
