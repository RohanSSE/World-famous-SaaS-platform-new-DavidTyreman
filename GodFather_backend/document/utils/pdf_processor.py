import PyPDF2
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF, handling both text and image-based PDFs"""
        text_content = []
        
        try:
            # First try standard text extraction
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    
                    # If no text or very little text, use OCR
                    if not text or len(text.strip()) < 50:
                        logger.info(f"Using OCR for page {page_num + 1}")
                        text = self._ocr_page(pdf_path, page_num)
                    
                    text_content.append({
                        'page': page_num + 1,
                        'text': text.strip()
                    })
            
            return text_content
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
    
    def _ocr_page(self, pdf_path, page_num):
        """Extract text from PDF page using OCR (Tesseract)"""
        try:
            images = convert_from_path(pdf_path, first_page=page_num + 1, last_page=page_num + 1)
            if images:
                text = pytesseract.image_to_string(images[0])
                return text
            return ""
        except Exception as e:
            logger.error(f"OCR error on page {page_num}: {str(e)}")
            return ""
    
    def chunk_text(self, text_content, document_id):
        """Split text into chunks with overlap"""
        chunks = []
        chunk_id = 0
        
        for page_data in text_content:
            page_num = page_data['page']
            text = page_data['text']
            words = text.split()
            
            if not words:
                continue
            
            for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
                chunk_words = words[i:i + self.chunk_size]
                chunk_text = ' '.join(chunk_words)
                
                chunks.append({
                    'document_id': document_id,
                    'chunk_id': chunk_id,
                    'text': chunk_text,
                    'page_number': page_num,
                    'metadata': {
                        'word_count': len(chunk_words),
                        'char_count': len(chunk_text)
                    }
                })
                chunk_id += 1
        
        return chunks
