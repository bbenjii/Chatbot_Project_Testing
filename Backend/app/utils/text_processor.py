# app/utils/text_processor.py
from typing import List, Dict, Any, Union
import logging
import io
from bs4 import BeautifulSoup
import PyPDF2
# import docx
import chardet
import re
from datetime import datetime, timezone
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class TextProcessor:
    def __init__(self):
        # Configure text splitter for consistent chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    async def extract_text(
            self,
            file_content: bytes,
            content_type: str,
    ) -> str:
        """Extract text from file bytes based on content type."""
        try:
            # Get the appropriate extractor based on content type
            if content_type == 'application/pdf':
                text_content = await self.extract_from_pdf_bytes(file_content)
            elif content_type == 'text/html':
                text_content = await self.extract_from_html_bytes(file_content)
            elif content_type == 'text/plain':
                text_content = await self.extract_from_text_bytes(file_content)
            # elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            #     text_content = await self.extract_from_docx_bytes(file_content)
            else:
                raise ValueError(f"Unsupported content type: {content_type}")

            # Clean the extracted text
            cleaned_text = self.sanitize_text(text_content)

            # Create metadata
            # metadata = {
            #     "source": filename,
            #     "content_type": content_type,
            #     "extraction_time": datetime.now(timezone.utc).isoformat(),
            #     "char_count": len(cleaned_text),
            #     "word_count": len(cleaned_text.split())
            # }

            # # Split into chunks and create Documents
            # chunks = self.text_splitter.create_documents(
            #     texts=[cleaned_text],
            #     metadatas=[metadata]
            # )

            return cleaned_text

        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            raise

    async def extract_from_pdf_bytes(self, file_content: bytes) -> str:
        """Extract text from PDF bytes."""
        try:
            text_content = []
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)

            return "\n\n".join(text_content)

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise

    async def extract_from_html_bytes(self, file_content: bytes) -> str:
        """Extract text from HTML bytes."""
        try:
            # Detect encoding
            encoding = chardet.detect(file_content)['encoding'] or 'utf-8'
            html_content = file_content.decode(encoding)

            # Parse HTML and extract text
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove unwanted elements
            for element in soup(['script', 'style', 'head', 'title', 'meta', '[document]']):
                element.decompose()

            # Get text and clean it
            return soup.get_text(separator=' ', strip=True)

        except Exception as e:
            logger.error(f"Error extracting text from HTML: {e}")
            raise

    async def extract_from_text_bytes(self, file_content: bytes) -> str:
        """Extract text from plain text bytes."""
        try:
            # Detect encoding
            encoding = chardet.detect(file_content)['encoding'] or 'utf-8'
            return file_content.decode(encoding)

        except Exception as e:
            logger.error(f"Error extracting text from plain text: {e}")
            raise

    # async def extract_from_docx_bytes(self, file_content: bytes) -> str:
    #     """Extract text from DOCX bytes."""
    #     try:
    #         docx_file = io.BytesIO(file_content)
    #         doc = docx.Document(docx_file)
    #
    #         # Extract text from paragraphs
    #         text_content = []
    #         for paragraph in doc.paragraphs:
    #             if paragraph.text.strip():
    #                 text_content.append(paragraph.text)
    #
    #         # Extract text from tables
    #         for table in doc.tables:
    #             for row in table.rows:
    #                 row_text = []
    #                 for cell in row.cells:
    #                     if cell.text.strip():
    #                         row_text.append(cell.text.strip())
    #                 if row_text:
    #                     text_content.append(" | ".join(row_text))
    #
    #         return "\n\n".join(text_content)
    #
    #     except Exception as e:
    #         logger.error(f"Error extracting text from DOCX: {e}")
    #         raise

    def sanitize_text(self, text: str) -> str:
        """Clean and sanitize text content."""
        try:
            # Replace multiple newlines with single newline
            text = re.sub(r'\n\s*\n', '\n\n', text)

            # Replace multiple spaces with single space
            text = re.sub(r'\s+', ' ', text)

            # Remove control characters except newlines
            text = ''.join(char for char in text if char == '\n' or char.isprintable())

            # Additional cleaning
            text = text.replace('\r', '')
            text = text.replace('\t', ' ')

            # Strip whitespace from each line
            lines = [line.strip() for line in text.split('\n')]
            text = '\n'.join(line for line in lines if line)

            return text.strip()

        except Exception as e:
            logger.error(f"Error sanitizing text: {e}")
            raise

    def get_text_stats(self, text: str) -> Dict[str, Any]:
        """Get statistics about the text content."""
        try:
            words = text.split()
            sentences = re.split(r'[.!?]+', text)

            return {
                'char_count': len(text),
                'word_count': len(words),
                'sentence_count': len(sentences),
                'average_word_length': sum(len(word) for word in words) / len(words) if words else 0,
                'average_sentence_length': len(words) / len(sentences) if sentences else 0
            }

        except Exception as e:
            logger.error(f"Error calculating text stats: {e}")
            raise

import asyncio

if __name__ == '__main__':
    async def main():
        cv_path = "../../Test-Documents/ben-resumes/benollomo-cv.pdf"
        cover_letter_path = "../../Test-Documents/ben-resumes/benollomo-cover-letter.pdf"
        goku_1_path = "../../Test-Documents/images/picolo.jpeg"


        file = None
        with open(cover_letter_path, "rb") as data:
            file = data.read()

        processor = TextProcessor()
        text_content = await processor.extract_text(file, "application/pdf")
        print(text_content)

    # asyncio.run(main())