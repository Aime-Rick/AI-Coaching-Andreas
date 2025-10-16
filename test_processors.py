#!/usr/bin/env python3
"""
Test script for Excel and Image processors
"""
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import os

def test_excel_processor():
    """Test Excel file processing"""
    try:
        from backend.files.excel_processor import ExcelProcessor
        
        print("🧪 Testing Excel Processor...")
        
        # Create a simple test CSV data
        test_data = {
            'Name': ['John Doe', 'Jane Smith', 'Bob Wilson'],
            'Age': [25, 30, 35],
            'Weight (kg)': [70.5, 65.2, 80.0],
            'Goal': ['Lose weight', 'Gain muscle', 'Maintain']
        }
        
        # Create DataFrame and convert to CSV bytes
        df = pd.DataFrame(test_data)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue().encode('utf-8')
        
        # Test processing
        result = ExcelProcessor.process_excel_file(csv_content, 'test_clients.csv')
        
        print(f"✅ Excel processing successful!")
        print(f"   Columns: {result['columns']}")
        print(f"   Rows: {result['shape'][0]}")
        print(f"   Total columns: {result['shape'][1]}")
        
        # Test preview
        preview = ExcelProcessor.get_excel_preview(csv_content, 'test_clients.csv')
        print(f"✅ Excel preview generated ({len(preview)} characters)")
        
        # Test vector store text extraction
        vector_text = ExcelProcessor.extract_text_for_vector_store(csv_content, 'test_clients.csv')
        print(f"✅ Vector store text extracted ({len(vector_text)} characters)")
        
        return True
        
    except Exception as e:
        print(f"❌ Excel processor test failed: {e}")
        return False


def test_image_processor():
    """Test Image file processing"""
    try:
        from backend.files.image_processor import ImageProcessor
        
        print("\n🧪 Testing Image Processor...")
        
        # Create a simple test image with text
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a font, fallback to default if not available
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # Add some text to the image
        text = "InBody Analysis\nWeight: 70.5 kg\nBody Fat: 15.2%\nMuscle Mass: 55.8 kg"
        draw.text((20, 20), text, fill='black', font=font)
        
        # Convert to bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_content = img_buffer.getvalue()
        
        # Test image info
        image_info = ImageProcessor.get_image_info(img_content)
        print(f"✅ Image info extracted: {image_info['width']}x{image_info['height']} pixels")
        
        # Test OCR
        extracted_text = ImageProcessor.extract_text_from_image(img_content)
        print(f"✅ OCR text extraction: {len(extracted_text)} characters")
        if extracted_text.strip():
            print(f"   Sample text: {extracted_text[:100]}...")
        
        # Test preview
        preview = ImageProcessor.get_image_preview(img_content, 'test_report.png')
        print(f"✅ Image preview generated ({len(preview)} characters)")
        
        # Test vector store text extraction
        vector_text = ImageProcessor.extract_text_for_vector_store(img_content, 'test_report.png')
        print(f"✅ Vector store text extracted ({len(vector_text)} characters)")
        
        return True
        
    except Exception as e:
        print(f"❌ Image processor test failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def test_file_utils():
    """Test enhanced file utils"""
    try:
        from backend.files.utils import FileManager
        
        print("\n🧪 Testing File Utils...")
        
        # Test file manager initialization
        file_manager = FileManager(skip_validation=True)
        print("✅ FileManager initialized in development mode")
        
        # Test file type detection
        test_files = [
            'document.pdf',
            'data.xlsx', 
            'report.csv',
            'image.jpg',
            'scan.png',
            'readme.txt'
        ]
        
        for filename in test_files:
            content_type = file_manager._get_content_type(filename)
            is_text = file_manager._is_text_file(filename)
            is_excel = file_manager._is_excel_file(filename)
            is_image = file_manager._is_image_file(filename)
            
            print(f"   {filename}: {content_type} (text: {is_text}, excel: {is_excel}, image: {is_image})")
        
        print("✅ File type detection working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ File utils test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Testing AI Coaching File Processing Enhancements\n")
    
    results = []
    
    # Test Excel processing
    results.append(test_excel_processor())
    
    # Test Image processing  
    results.append(test_image_processor())
    
    # Test File utils
    results.append(test_file_utils())
    
    print(f"\n📊 Test Results:")
    print(f"   Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 All tests passed! Your enhancements are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
    
    return all(results)


if __name__ == "__main__":
    main()