"""
Image processing utilities for extracting text and analyzing images
"""
import io
import base64
from typing import Dict, Any, Optional
from PIL import Image
import pytesseract
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ImageProcessor:
    @staticmethod
    def extract_text_from_image(image_content: bytes) -> str:
        """
        Extract text from image using advanced OCR preprocessing (useful for InBody reports, meal plans)
        
        Args:
            image_content: Raw image content as bytes
            
        Returns:
            Extracted text string
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_content))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Advanced preprocessing for better OCR results
            # Convert PIL image to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Store original for fallback
            original_cv = cv_image.copy()
            
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Advanced preprocessing pipeline
            processed_images = []
            
            # Method 1: Basic preprocessing
            # Denoise
            denoised = cv2.medianBlur(gray, 3)
            # Increase contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            contrast_enhanced = clahe.apply(denoised)
            processed_images.append(("basic", contrast_enhanced))
            
            # Method 2: Morphological operations for text enhancement
            # Create kernel for morphological operations
            kernel = np.ones((2,2), np.uint8)
            # Apply morphological opening to remove noise
            morph_open = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel, iterations=1)
            # Apply morphological closing to fill gaps
            morph_close = cv2.morphologyEx(morph_open, cv2.MORPH_CLOSE, kernel, iterations=1)
            processed_images.append(("morphological", morph_close))
            
            # Method 3: Gaussian blur + thresholding
            # Apply Gaussian blur to smooth the image
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            # Apply adaptive thresholding
            thresh_adaptive = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            processed_images.append(("adaptive_thresh", thresh_adaptive))
            
            # Method 4: Otsu's thresholding
            # Apply Otsu's threshold for automatic binarization
            blurred_otsu = cv2.GaussianBlur(gray, (3, 3), 0)
            _, thresh_otsu = cv2.threshold(blurred_otsu, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_images.append(("otsu", thresh_otsu))
            
            # Method 5: Edge-preserving filter + sharpening
            # Apply bilateral filter to reduce noise while preserving edges
            bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
            # Apply unsharp mask for sharpening
            gaussian = cv2.GaussianBlur(bilateral, (0, 0), 2.0)
            sharpened = cv2.addWeighted(bilateral, 1.5, gaussian, -0.5, 0)
            processed_images.append(("sharpened", sharpened))
            
            # Method 6: For very noisy images - advanced denoising
            # Apply Non-local Means Denoising
            nlm_denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            processed_images.append(("nlm_denoised", nlm_denoised))
            
            # OCR configurations optimized for different document types
            ocr_configs = [
                ('default', '--oem 3 --psm 6'),  # Default configuration
                ('single_column', '--oem 3 --psm 4'),  # Single column of text
                ('auto_page', '--oem 3 --psm 3'),  # Fully automatic page segmentation
                ('sparse_text', '--oem 3 --psm 11'),  # Sparse text
                ('single_line', '--oem 3 --psm 13'),  # Raw line
                ('single_word', '--oem 3 --psm 8'),   # Single word
                ('vertical_text', '--oem 3 --psm 5'),  # Vertical text
                ('uniform_block', '--oem 3 --psm 7'),  # Uniform block of text
                ('numbers_only', '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.,% '),  # Numbers only
                ('alphanumeric', '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,:%/- ')
            ]
            
            best_result = ""
            best_confidence = 0
            best_method = ""
            
            # Try each preprocessing method with each OCR configuration
            for img_name, processed_img in processed_images:
                for config_name, config in ocr_configs:
                    try:
                        # Get text with confidence scores
                        data = pytesseract.image_to_data(
                            processed_img, 
                            config=config, 
                            output_type=pytesseract.Output.DICT
                        )
                        
                        # Calculate average confidence for non-empty text
                        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                        
                        # Get the text
                        result = pytesseract.image_to_string(processed_img, config=config)
                        
                        # Score based on text length and confidence
                        score = len(result.strip()) * (avg_confidence / 100)
                        
                        if score > best_confidence and len(result.strip()) > 5:
                            best_result = result
                            best_confidence = score
                            best_method = f"{img_name}+{config_name}"
                            
                    except Exception as e:
                        continue
            
            # If still no good result, try with original image and simple config
            if len(best_result.strip()) < 10:
                try:
                    best_result = pytesseract.image_to_string(image, config='--oem 3 --psm 6')
                    best_method = "original_fallback"
                except Exception:
                    best_result = "No text detected"
                    best_method = "failed"
            
            # Log the best method for debugging
            logger.info(f"OCR completed using method: {best_method}, confidence score: {best_confidence:.2f}")
            
            return best_result.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {str(e)}")
            return f"Error extracting text from image: {str(e)}"
    
    @staticmethod
    def debug_ocr_preprocessing(image_content: bytes, output_dir: str = "/tmp/ocr_debug") -> Dict[str, Any]:
        """
        Debug OCR preprocessing by saving intermediate images and testing different methods
        
        Args:
            image_content: Raw image content as bytes
            output_dir: Directory to save debug images
            
        Returns:
            Dictionary with results from different preprocessing methods
        """
        try:
            import os
            os.makedirs(output_dir, exist_ok=True)
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_content))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert PIL image to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Save original
            cv2.imwrite(f"{output_dir}/01_original.png", cv_image)
            cv2.imwrite(f"{output_dir}/02_grayscale.png", gray)
            
            results = {}
            
            # Test different preprocessing methods
            methods = []
            
            # Basic preprocessing
            denoised = cv2.medianBlur(gray, 3)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            contrast_enhanced = clahe.apply(denoised)
            cv2.imwrite(f"{output_dir}/03_basic_enhanced.png", contrast_enhanced)
            methods.append(("basic", contrast_enhanced))
            
            # Morphological operations
            kernel = np.ones((2,2), np.uint8)
            morph_open = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel, iterations=1)
            morph_close = cv2.morphologyEx(morph_open, cv2.MORPH_CLOSE, kernel, iterations=1)
            cv2.imwrite(f"{output_dir}/04_morphological.png", morph_close)
            methods.append(("morphological", morph_close))
            
            # Adaptive thresholding
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            thresh_adaptive = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            cv2.imwrite(f"{output_dir}/05_adaptive_thresh.png", thresh_adaptive)
            methods.append(("adaptive_thresh", thresh_adaptive))
            
            # Otsu's thresholding
            blurred_otsu = cv2.GaussianBlur(gray, (3, 3), 0)
            _, thresh_otsu = cv2.threshold(blurred_otsu, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            cv2.imwrite(f"{output_dir}/06_otsu.png", thresh_otsu)
            methods.append(("otsu", thresh_otsu))
            
            # Sharpened
            bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
            gaussian = cv2.GaussianBlur(bilateral, (0, 0), 2.0)
            sharpened = cv2.addWeighted(bilateral, 1.5, gaussian, -0.5, 0)
            cv2.imwrite(f"{output_dir}/07_sharpened.png", sharpened)
            methods.append(("sharpened", sharpened))
            
            # Test OCR on each method
            for method_name, processed_img in methods:
                try:
                    # Get text with confidence
                    data = pytesseract.image_to_data(
                        processed_img, 
                        config='--oem 3 --psm 6', 
                        output_type=pytesseract.Output.DICT
                    )
                    
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    
                    text = pytesseract.image_to_string(processed_img, config='--oem 3 --psm 6')
                    
                    results[method_name] = {
                        'text': text.strip(),
                        'confidence': avg_confidence,
                        'text_length': len(text.strip()),
                        'image_saved': f"{output_dir}/{method_name}.png"
                    }
                    
                except Exception as e:
                    results[method_name] = {
                        'error': str(e),
                        'image_saved': f"{output_dir}/{method_name}.png"
                    }
            
            # Find best result
            best_method = max(
                [k for k, v in results.items() if 'text' in v],
                key=lambda k: results[k]['text_length'] * (results[k]['confidence'] / 100),
                default=None
            )
            
            results['summary'] = {
                'best_method': best_method,
                'debug_images_saved_to': output_dir,
                'total_methods_tested': len(methods)
            }
            
            return results
            
        except Exception as e:
            return {'error': f"Debug preprocessing failed: {str(e)}"}

    @staticmethod
    def get_image_info(image_content: bytes) -> Dict[str, Any]:
        """
        Get detailed image information and metadata
        
        Args:
            image_content: Raw image content as bytes
            
        Returns:
            Dictionary with image metadata
        """
        try:
            image = Image.open(io.BytesIO(image_content))
            
            info = {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'width': image.width,
                'height': image.height,
                'has_transparency': image.mode in ('RGBA', 'LA') or 'transparency' in image.info,
                'file_size_bytes': len(image_content),
                'file_size_mb': round(len(image_content) / (1024 * 1024), 2)
            }
            
            # Add EXIF data if available
            try:
                exif_data = image._getexif()
                if exif_data:
                    info['has_exif'] = True
                    info['exif_keys'] = len(exif_data.keys())
                else:
                    info['has_exif'] = False
            except:
                info['has_exif'] = False
            
            return info
            
        except Exception as e:
            logger.error(f"Could not analyze image: {str(e)}")
            return {'error': f"Could not analyze image: {str(e)}"}
    
    @staticmethod
    def analyze_with_openai_vision(image_content: bytes, client, custom_prompt: Optional[str] = None) -> str:
        """
        Analyze image using OpenAI's vision capabilities
        
        Args:
            image_content: Raw image content as bytes
            client: OpenAI client instance
            custom_prompt: Optional custom analysis prompt
            
        Returns:
            AI analysis of the image
        """
        try:
            # Convert to base64
            base64_image = base64.b64encode(image_content).decode('utf-8')
            
            # Default prompt for health/fitness context
            default_prompt = """
            Analyze this image and extract any relevant information. Pay special attention to:
            - Medical reports or body composition analysis (like InBody reports)
            - Meal plans, nutrition information, or food-related content
            - Exercise routines or fitness-related information
            - Health metrics, measurements, or tracking data
            - Any text, numbers, charts, or structured data
            
            Provide a detailed analysis including any specific values, measurements, or recommendations you can identify.
            """
            
            prompt = custom_prompt if custom_prompt else default_prompt
            
            # Use OpenAI Vision API
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error analyzing image with AI: {str(e)}")
            return f"Error analyzing image with AI: {str(e)}"
    
    @staticmethod
    def get_image_preview(image_content: bytes, filename: str) -> str:
        """
        Generate a comprehensive preview of an image file
        
        Args:
            image_content: Raw image content as bytes
            filename: Name of the image file
            
        Returns:
            Formatted preview string
        """
        try:
            # Get image info
            image_info = ImageProcessor.get_image_info(image_content)
            
            # Extract text using OCR
            extracted_text = ImageProcessor.extract_text_from_image(image_content)
            
            preview_lines = []
            preview_lines.append(f"🖼️  Image File: {filename}")
            
            if 'error' in image_info:
                preview_lines.append(f"❌ Error: {image_info['error']}")
            else:
                preview_lines.append(f"📐 Format: {image_info.get('format', 'Unknown')}")
                preview_lines.append(f"📏 Dimensions: {image_info.get('width', 'Unknown')} x {image_info.get('height', 'Unknown')} pixels")
                preview_lines.append(f"💾 Size: {image_info.get('file_size_mb', 'Unknown')} MB")
                preview_lines.append(f"🎨 Mode: {image_info.get('mode', 'Unknown')}")
                if image_info.get('has_exif'):
                    preview_lines.append(f"📊 EXIF Data: Available ({image_info.get('exif_keys', 0)} fields)")
            
            preview_lines.append("")
            
            if extracted_text and len(extracted_text.strip()) > 0:
                preview_lines.append("📝 Extracted Text (OCR):")
                preview_lines.append("─" * 40)
                # Limit text length for preview
                text_lines = extracted_text.split('\n')
                for i, line in enumerate(text_lines[:20]):  # Show first 20 lines
                    if line.strip():
                        preview_lines.append(line.strip())
                
                if len(text_lines) > 20:
                    preview_lines.append(f"... and {len(text_lines) - 20} more lines")
            else:
                preview_lines.append("📝 No text detected in image")
            
            return "\n".join(preview_lines)
            
        except Exception as e:
            logger.error(f"Error creating image preview for {filename}: {str(e)}")
            return f"❌ Error processing image file: {str(e)}"
    
    @staticmethod
    def extract_text_for_vector_store(image_content: bytes, filename: str) -> str:
        """
        Extract and format image content for vector store processing
        
        Args:
            image_content: Raw image content as bytes
            filename: Name of the image file
            
        Returns:
            Text representation suitable for vector store
        """
        try:
            # Get image metadata
            image_info = ImageProcessor.get_image_info(image_content)
            
            # Extract text content
            extracted_text = ImageProcessor.extract_text_from_image(image_content)
            
            # Format for vector store
            text_parts = []
            
            # File metadata
            text_parts.append(f"Document: {filename}")
            text_parts.append(f"Type: Image File ({image_info.get('format', 'Unknown')})")
            text_parts.append(f"Dimensions: {image_info.get('width', 'Unknown')} x {image_info.get('height', 'Unknown')} pixels")
            text_parts.append("")
            
            # Content description
            text_parts.append("Image Content Analysis:")
            if extracted_text and len(extracted_text.strip()) > 0:
                text_parts.append("Extracted Text Content:")
                text_parts.append(extracted_text)
            else:
                text_parts.append("This is an image file with no detectable text content.")
                text_parts.append("The image may contain visual information such as charts, graphs, photos, or diagrams.")
            
            return "\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"Error extracting image text for vector store {filename}: {str(e)}")
            return f"Image file {filename}: Error processing content - {str(e)}"
    
    @staticmethod
    def is_image_file(filename: str) -> bool:
        """
        Check if a file is an image file
        
        Args:
            filename: Name of the file
            
        Returns:
            True if file is an image, False otherwise
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp', '.ico'}
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        return f'.{file_ext}' in image_extensions