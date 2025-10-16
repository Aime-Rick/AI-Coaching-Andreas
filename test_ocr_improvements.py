#!/usr/bin/env python3
"""
Test improved OCR accuracy with advanced preprocessing
"""
import sys
sys.path.insert(0, '/home/ricko/AI-Coaching-Andreas')

from backend.files.image_processor import ImageProcessor
from PIL import Image, ImageDraw, ImageFont
import io
import time


def create_test_images():
    """Create various test images to demonstrate OCR improvements"""
    test_images = []
    
    # Test 1: Clean, high-contrast text (should work well)
    img1 = Image.new('RGB', (600, 200), color='white')
    draw1 = ImageDraw.Draw(img1)
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font_large = ImageFont.load_default()
    
    text1 = """InBody Analysis Report
Patient: John Doe  Weight: 75.2 kg
Body Fat: 17.0%  Muscle Mass: 34.5 kg"""
    draw1.text((20, 20), text1, fill='black', font=font_large)
    
    img1_buffer = io.BytesIO()
    img1.save(img1_buffer, format='PNG')
    test_images.append(("clean_text", img1_buffer.getvalue()))
    
    # Test 2: Noisy, low-contrast text (challenging)
    img2 = Image.new('RGB', (600, 200), color='#f0f0f0')  # Light gray background
    draw2 = ImageDraw.Draw(img2)
    
    text2 = """Weight: 68.5kg BMI: 23.1
Body Fat: 15.2% Muscle: 52.8kg
Recommendation: Increase protein"""
    draw2.text((20, 20), text2, fill='#404040', font=font_large)  # Dark gray text
    
    # Add some noise
    import random
    pixels = img2.load()
    for i in range(50):  # Add random noise dots
        x, y = random.randint(0, 599), random.randint(0, 199)
        pixels[x, y] = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
    
    img2_buffer = io.BytesIO()
    img2.save(img2_buffer, format='PNG')
    test_images.append(("noisy_text", img2_buffer.getvalue()))
    
    # Test 3: Small text (challenging for OCR)
    img3 = Image.new('RGB', (400, 300), color='white')
    draw3 = ImageDraw.Draw(img3)
    try:
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font_small = ImageFont.load_default()
    
    text3 = """Detailed Body Composition Analysis
Date: 2024-10-16
Patient ID: 12345

Measurements:
Height: 175.5 cm
Weight: 75.2 kg
BMI: 24.4 kg/m²

Body Composition:
Total Body Water: 45.2 L (60.1%)
Protein: 11.8 kg (15.7%)
Minerals: 3.2 kg (4.3%)
Body Fat Mass: 15.0 kg (19.9%)

Segmental Muscle Analysis:
Right Arm: 3.2 kg
Left Arm: 3.1 kg
Trunk: 24.8 kg
Right Leg: 8.9 kg
Left Leg: 8.8 kg"""
    
    draw3.text((10, 10), text3, fill='black', font=font_small)
    
    img3_buffer = io.BytesIO()
    img3.save(img3_buffer, format='PNG')
    test_images.append(("small_text", img3_buffer.getvalue()))
    
    return test_images


def test_ocr_improvements():
    """Test OCR with different image types"""
    print("🔬 TESTING IMPROVED OCR ACCURACY")
    print("=" * 60)
    
    test_images = create_test_images()
    
    total_improvements = 0
    
    for img_name, img_content in test_images:
        print(f"\n📷 Testing: {img_name}")
        print("-" * 40)
        
        start_time = time.time()
        extracted_text = ImageProcessor.extract_text_from_image(img_content)
        processing_time = time.time() - start_time
        
        print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        print(f"📝 Extracted text ({len(extracted_text)} characters):")
        print(f"   {extracted_text[:200]}..." if len(extracted_text) > 200 else f"   {extracted_text}")
        
        # Analyze quality indicators
        words = extracted_text.split()
        numeric_matches = sum(1 for word in words if any(char.isdigit() for char in word))
        
        print(f"📊 Quality indicators:")
        print(f"   - Total characters: {len(extracted_text)}")
        print(f"   - Words detected: {len(words)}")
        print(f"   - Numeric values: {numeric_matches}")
        
        # Expected keywords for each test
        expected_keywords = {
            "clean_text": ["InBody", "Patient", "John", "Weight", "75.2", "Body Fat", "17.0", "Muscle"],
            "noisy_text": ["Weight", "68.5", "BMI", "23.1", "Body Fat", "15.2", "protein"],
            "small_text": ["Composition", "Height", "175.5", "BMI", "24.4", "Segmental", "Right Arm"]
        }
        
        if img_name in expected_keywords:
            found_keywords = sum(1 for keyword in expected_keywords[img_name] if keyword.lower() in extracted_text.lower())
            accuracy = (found_keywords / len(expected_keywords[img_name])) * 100
            print(f"   - Keyword accuracy: {found_keywords}/{len(expected_keywords[img_name])} ({accuracy:.1f}%)")
            
            if accuracy > 70:
                print("   ✅ GOOD accuracy")
            elif accuracy > 40:
                print("   ⚠️  MODERATE accuracy")
            else:
                print("   ❌ LOW accuracy")


def explain_improvements():
    """Explain what improvements were made"""
    print("\n🚀 OCR IMPROVEMENTS IMPLEMENTED")
    print("=" * 60)
    
    improvements = [
        "🔍 Multiple Preprocessing Methods:",
        "   • CLAHE (Contrast Limited Adaptive Histogram Equalization)",
        "   • Morphological operations (opening/closing)",
        "   • Adaptive thresholding",
        "   • Otsu's automatic thresholding",
        "   • Bilateral filtering + unsharp masking",
        "   • Non-local means denoising",
        "",
        "⚙️  Advanced OCR Configuration:",
        "   • 10 different PSM (Page Segmentation Mode) settings",
        "   • Character whitelisting for numbers/text",
        "   • Confidence-based result selection",
        "   • Multiple method combination testing",
        "",
        "📊 Smart Selection Algorithm:",
        "   • Tests each preprocessing method with each OCR config",
        "   • Calculates confidence scores for each result",
        "   • Selects best result based on text length + confidence",
        "   • Falls back gracefully if no good results found",
        "",
        "🐛 Debug Capabilities:",
        "   • Save intermediate processing images",
        "   • Compare results from different methods",
        "   • Identify which preprocessing works best for specific image types"
    ]
    
    for improvement in improvements:
        print(improvement)


def provide_tips():
    """Provide tips for better OCR results"""
    print("\n💡 TIPS FOR BETTER OCR ACCURACY")
    print("=" * 60)
    
    tips = [
        "📸 Image Quality:",
        "   • Use high resolution images (300+ DPI)",
        "   • Ensure good lighting and contrast",
        "   • Avoid blurry or out-of-focus images",
        "   • Keep text horizontal (not rotated)",
        "",
        "📄 Document Preparation:",
        "   • Scan documents in color or high-quality grayscale",
        "   • Remove shadows and glare",
        "   • Use a scanner instead of phone camera when possible",
        "   • Ensure text is not too small (minimum 12pt font)",
        "",
        "🔧 System Usage:",
        "   • Use /files/debug-ocr endpoint to test different preprocessing",
        "   • For medical reports, ensure high contrast between text and background",
        "   • For tables/spreadsheets, ensure clear cell boundaries",
        "   • For handwritten text, consider using AI vision instead of OCR"
    ]
    
    for tip in tips:
        print(tip)


def main():
    """Run the complete OCR improvement demonstration"""
    test_ocr_improvements()
    explain_improvements()
    provide_tips()
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY")
    print("✅ Enhanced OCR with 6 preprocessing methods")
    print("✅ 10 different OCR configurations tested automatically")
    print("✅ Confidence-based selection for best results")
    print("✅ Debug tools available for troubleshooting")
    print("✅ Optimized for medical reports and fitness documents")
    print("")
    print("🔗 API Endpoints:")
    print("   • POST /files/analyze-image - Full AI + OCR analysis")
    print("   • POST /files/debug-ocr - Debug OCR processing issues")


if __name__ == "__main__":
    main()