"""
PDF Processor Utility
======================
Handles PDF text extraction, chunking, and embedding generation.

This module:
1. Extracts text from PDF files using PyPDF2
2. Splits text into manageable chunks
3. Creates text embeddings for vector search
"""

import os
from typing import List, Dict, Any

# PDF reading library
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

# LangChain for text splitting
from langchain.text_splitter import RecursiveCharacterTextSplitter


class PDFProcessor:
    """
    Handles all PDF-related operations.
    
    Usage:
        processor = PDFProcessor()
        result = processor.process_pdf('path/to/file.pdf')
    """

    def __init__(self):
        # Store the full extracted text
        self._full_text = ""
        self._is_processed = False

        # Text splitter configuration
        # chunk_size: how many characters per chunk
        # chunk_overlap: how many chars overlap between chunks (for context)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    def process_pdf(self, filepath: str) -> Dict[str, Any]:
        """
        Main method to process a PDF file.
        
        Steps:
        1. Extract text from all pages
        2. Clean the text
        3. Split into chunks
        
        Returns a dict with success status, chunks, and metadata.
        """
        try:
            # Step 1: Extract text
            text, page_count = self._extract_text(filepath)

            if not text.strip():
                return {
                    'success': False,
                    'error': 'Could not extract text from PDF. The file may be scanned or image-based.'
                }

            # Step 2: Clean the text
            cleaned_text = self._clean_text(text)

            # Step 3: Store full text for summarization
            self._full_text = cleaned_text
            self._is_processed = True

            # Step 4: Split into chunks for vector search
            chunks = self.text_splitter.split_text(cleaned_text)

            return {
                'success': True,
                'chunks': chunks,
                'page_count': page_count,
                'chunk_count': len(chunks),
                'text_length': len(cleaned_text)
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'PDF processing error: {str(e)}'
            }

    def _extract_text(self, filepath: str):
        """
        Extract text from PDF using available library.
        Tries pdfplumber first (better quality), falls back to PyPDF2.
        """
        text = ""
        page_count = 0

        # Try pdfplumber first (usually better text extraction)
        if pdfplumber:
            try:
                with pdfplumber.open(filepath) as pdf:
                    page_count = len(pdf.pages)
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n\n"
                if text.strip():
                    return text, page_count
            except Exception:
                pass  # Fall through to PyPDF2

        # Fall back to PyPDF2
        if PyPDF2:
            with open(filepath, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                page_count = len(reader.pages)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"

        return text, page_count

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing extra whitespace and fixing common issues.
        """
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            # Strip leading/trailing whitespace from each line
            line = line.strip()
            # Skip empty lines (but keep paragraph breaks)
            cleaned_lines.append(line)

        # Join lines and remove excessive blank lines
        text = '\n'.join(cleaned_lines)

        # Replace multiple consecutive newlines with double newline
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def has_text(self) -> bool:
        """Check if a PDF has been processed and text is available."""
        return self._is_processed and bool(self._full_text)

    def get_full_text(self) -> str:
        """Return the full extracted text."""
        return self._full_text

    def reset(self):
        """Reset the processor (clear stored text)."""
        self._full_text = ""
        self._is_processed = False
