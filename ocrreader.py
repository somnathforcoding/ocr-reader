import os
import sys
from PIL import Image
import pytesseract
import pdf2image
from pathlib import Path
import re
from collections import Counter
import argparse

class OCRProcessor:
    def __init__(self):
        # Configure tesseract path if needed (Windows users might need to set this)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
    
    def extract_text_from_image(self, image_path):
        """Extract text from a single image file"""
        try:
            # Open and process the image
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(image, lang='eng')
            return text.strip()
            
        except Exception as e:
            print(f"Error processing image {image_path}: {str(e)}")
            return ""
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF by converting pages to images"""
        try:
            # Convert PDF pages to images
            pages = pdf2image.convert_from_path(pdf_path, dpi=300)
            
            extracted_text = ""
            for i, page in enumerate(pages):
                print(f"Processing page {i+1}/{len(pages)}...")
                
                # Extract text from each page
                page_text = pytesseract.image_to_string(page, lang='eng')
                extracted_text += f"\n--- Page {i+1} ---\n"
                extracted_text += page_text.strip() + "\n"
            
            return extracted_text.strip()
            
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {str(e)}")
            return ""
    
    def clean_text(self, text):
        """Clean and normalize extracted text"""
        # Remove extra whitespace and normalize line breaks
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r' +', ' ', text)
        text = text.strip()
        return text
    
    def analyze_content(self, text):
        """Analyze and describe the extracted text content"""
        if not text:
            return "No text could be extracted from the file."
        
        # Basic statistics
        word_count = len(text.split())
        char_count = len(text)
        line_count = len(text.split('\n'))
        
        # Find common words (excluding common stop words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        common_words = Counter(filtered_words).most_common(10)
        
        # Detect potential content type
        content_type = self.detect_content_type(text)
        
        # Generate description
        description = f"""
TEXT ANALYSIS REPORT
===================

Content Type: {content_type}

Statistics:
- Word Count: {word_count}
- Character Count: {char_count}
- Line Count: {line_count}

Most Common Words:
{chr(10).join([f"- {word}: {count}" for word, count in common_words])}

Content Preview (first 200 characters):
{text[:200]}{'...' if len(text) > 200 else ''}

Full Extracted Text:
{'-' * 50}
{text}
"""
        
        return description
    
    def detect_content_type(self, text):
        """Attempt to detect the type of content based on text patterns"""
        text_lower = text.lower()
        
        # Check for various content indicators
        if any(word in text_lower for word in ['invoice', 'bill', 'amount', 'total', 'payment']):
            return "Financial Document/Invoice"
        elif any(word in text_lower for word in ['dear', 'sincerely', 'regards', 'letter']):
            return "Letter/Correspondence"
        elif any(word in text_lower for word in ['recipe', 'ingredients', 'instructions', 'cooking']):
            return "Recipe"
        elif any(word in text_lower for word in ['article', 'paragraph', 'section', 'chapter']):
            return "Article/Document"
        elif any(word in text_lower for word in ['menu', 'price', 'restaurant', 'food']):
            return "Menu"
        elif re.search(r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b', text):
            return "Document with Dates"
        elif re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
            return "Document with Email Addresses"
        else:
            return "General Text Document"
    
    def process_file(self, input_path, output_path=None):
        """Process a file and extract text with description"""
        input_path = Path(input_path)
        
        if not input_path.exists():
            print(f"Error: File {input_path} does not exist.")
            return False
        
        # Determine output path
        if output_path is None:
            output_path = input_path.with_suffix('.txt')
        
        print(f"Processing: {input_path}")
        print(f"Output will be saved to: {output_path}")
        
        # Extract text based on file type
        file_extension = input_path.suffix.lower()
        
        if file_extension == '.pdf':
            extracted_text = self.extract_text_from_pdf(input_path)
        elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']:
            extracted_text = self.extract_text_from_image(input_path)
        else:
            print(f"Error: Unsupported file type {file_extension}")
            return False
        
        # Clean the extracted text
        cleaned_text = self.clean_text(extracted_text)
        
        # Analyze and describe the content
        description = self.analyze_content(cleaned_text)
        
        # Save to text file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(description)
            
            print(f"Successfully saved extracted text and analysis to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Extract text from images and PDFs using OCR')
    parser.add_argument('input_file', help='Path to input file (JPG, PNG, PDF)')
    parser.add_argument('-o', '--output', help='Output text file path (optional)')
    
    args = parser.parse_args()
    
    # Create OCR processor
    processor = OCRProcessor()
    
    # Process the file
    success = processor.process_file(args.input_file, args.output)
    
    if success:
        print("\nOCR processing completed successfully!")
    else:
        print("\nOCR processing failed.")
        sys.exit(1)

if __name__ == "__main__":
    # Example usage if run directly
    if len(sys.argv) < 2:
        print("Usage: python ocr_tool.py <input_file> [-o output_file]")
        print("Example: python ocr_tool.py document.pdf")
        print("Example: python ocr_tool.py image.jpg -o extracted_text.txt")
        sys.exit(1)
    
    main()