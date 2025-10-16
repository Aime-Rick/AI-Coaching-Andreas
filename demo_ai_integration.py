#!/usr/bin/env python3
"""
Demo script showing how Excel and Image files are processed for AI chat sessions
"""
import sys
import os

# Add the project root to the path so we can import our modules
sys.path.insert(0, '/home/ricko/AI-Coaching-Andreas')

from backend.files.excel_processor import ExcelProcessor
from backend.files.image_processor import ImageProcessor
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io


def demo_excel_processing():
    """Show what happens when Excel files are added to vector store"""
    print("🔹 EXCEL FILE PROCESSING DEMO")
    print("=" * 50)
    
    # Create sample client data (meal plan)
    meal_plan_data = {
        'Meal': ['Breakfast', 'Snack', 'Lunch', 'Snack', 'Dinner'],
        'Food': ['Oatmeal with berries', 'Greek yogurt', 'Grilled chicken salad', 'Apple with almonds', 'Salmon with vegetables'],
        'Calories': [350, 150, 450, 200, 400],
        'Protein_g': [12, 15, 35, 5, 30],
        'Carbs_g': [65, 8, 25, 25, 20],
        'Fat_g': [8, 8, 18, 12, 18]
    }
    
    # Convert to CSV format
    df = pd.DataFrame(meal_plan_data)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue().encode('utf-8')
    
    # Process for vector store (this is what happens automatically when you start a session)
    vector_text = ExcelProcessor.extract_text_for_vector_store(csv_content, 'client_meal_plan.csv')
    
    print("📄 Original Excel/CSV Data:")
    print(df.to_string())
    
    print("\n🔍 Text extracted for AI (vector store):")
    print("-" * 40)
    print(vector_text[:500] + "..." if len(vector_text) > 500 else vector_text)
    
    print(f"\n✅ The AI can now answer questions like:")
    print("   • 'What did the client eat for breakfast?'")
    print("   • 'How many calories are in the meal plan?'")
    print("   • 'What's the protein content of lunch?'")
    print("   • 'Analyze the nutritional balance of this meal plan'")
    
    return vector_text


def demo_image_processing():
    """Show what happens when image files are added to vector store"""
    print("\n🔹 IMAGE FILE PROCESSING DEMO")
    print("=" * 50)
    
    # Create sample InBody report image
    img = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a font
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    # Add realistic InBody report content
    report_text = """InBody Analysis Report
    
Patient: John Doe
Date: 2024-10-16

Body Composition:
Weight: 75.2 kg
Body Fat Mass: 12.8 kg (17.0%)
Skeletal Muscle Mass: 34.5 kg
Total Body Water: 45.2 L

Segmental Analysis:
Right Arm Muscle: 3.2 kg
Left Arm Muscle: 3.1 kg  
Trunk Muscle: 24.8 kg
Right Leg Muscle: 8.9 kg
Left Leg Muscle: 8.8 kg

Recommended Goals:
- Increase muscle mass by 2-3 kg
- Maintain current body fat percentage
- Focus on leg muscle development"""
    
    # Draw the text on the image
    y_position = 20
    for line in report_text.split('\n'):
        if line.strip():
            if line.startswith('InBody') or line.startswith('Patient') or line.startswith('Date'):
                draw.text((20, y_position), line.strip(), fill='black', font=font_large)
                y_position += 30
            else:
                draw.text((20, y_position), line.strip(), fill='black', font=font_medium)
                y_position += 22
    
    # Convert to bytes
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_content = img_buffer.getvalue()
    
    # Process for vector store (this happens automatically when you start a session)
    vector_text = ImageProcessor.extract_text_for_vector_store(img_content, 'john_doe_inbody_report.png')
    
    print("🖼️  Simulated InBody Report Image Created")
    print(f"   Size: 600x400 pixels, {len(img_content)} bytes")
    
    print("\n🔍 Text extracted for AI (OCR + vector store):")
    print("-" * 40)
    print(vector_text)
    
    print(f"\n✅ The AI can now answer questions like:")
    print("   • 'What is John's current body fat percentage?'")
    print("   • 'How much skeletal muscle mass does he have?'")
    print("   • 'What are the recommended goals from his InBody report?'")
    print("   • 'Compare his right and left leg muscle mass'")
    print("   • 'Create a training plan based on his body composition'")
    
    return vector_text


def demo_session_workflow():
    """Show the complete workflow when starting a session with mixed files"""
    print("\n🔹 COMPLETE SESSION WORKFLOW")
    print("=" * 50)
    
    print("When you start a chat session with a folder containing:")
    print("📂 Client_Files/")
    print("   ├── 📄 meal_plan.xlsx        (Excel file)")
    print("   ├── 🖼️  inbody_report.jpg     (Image file)")
    print("   ├── 📝 notes.txt            (Text file)")
    print("   └── 📋 progress_tracking.csv (CSV file)")
    
    print("\n🔄 Automatic Processing Steps:")
    print("1. 🔍 System scans folder and identifies file types")
    print("2. 📊 Excel/CSV files → Extract structured data (tables, columns, values)")
    print("3. 🖼️  Image files → OCR text extraction + AI vision analysis")
    print("4. 📝 Text files → Direct content extraction")
    print("5. 🧠 All content → Upload to OpenAI vector store")
    print("6. ✅ AI assistant ready with comprehensive knowledge of all files")
    
    print("\n💬 Example AI Capabilities:")
    print("User: 'Based on John's InBody report and meal plan, what changes do you recommend?'")
    print("AI: 'Looking at John's InBody report showing 17% body fat and his current meal plan...")
    print("     I can see his breakfast has 350 calories with 12g protein. Given his goal to...")
    print("     increase muscle mass by 2-3kg, I recommend increasing his protein intake...'")
    
    print("\nUser: 'How many total calories is he eating per day according to his meal plan?'")
    print("AI: 'According to the meal plan CSV, John's daily intake is:")
    print("     Breakfast: 350 + Snack: 150 + Lunch: 450 + Snack: 200 + Dinner: 400 = 1,550 calories'")


def main():
    """Run the complete demonstration"""
    print("🚀 AI COACHING - EXCEL & IMAGE INTEGRATION DEMO")
    print("=" * 60)
    print("This shows how Excel and Image files are automatically processed")
    print("when you start a chat session with a folder containing mixed file types.\n")
    
    # Demo Excel processing
    excel_vector_text = demo_excel_processing()
    
    # Demo Image processing  
    image_vector_text = demo_image_processing()
    
    # Demo complete workflow
    demo_session_workflow()
    
    print("\n" + "=" * 60)
    print("🎯 KEY BENEFITS:")
    print("✅ No manual file conversion needed")
    print("✅ AI automatically understands Excel data structure") 
    print("✅ OCR extracts text from images (InBody reports, scanned documents)")
    print("✅ All file content is searchable and queryable by AI")
    print("✅ AI can correlate data across multiple files")
    print("✅ Natural language questions about technical data")
    
    print(f"\n📊 PROCESSING STATS:")
    print(f"Excel vector text: {len(excel_vector_text)} characters")
    print(f"Image vector text: {len(image_vector_text)} characters")
    print(f"Total content available to AI: {len(excel_vector_text) + len(image_vector_text)} characters")


if __name__ == "__main__":
    main()