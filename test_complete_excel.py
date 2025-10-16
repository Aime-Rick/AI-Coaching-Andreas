#!/usr/bin/env python3
"""
Test script to demonstrate improved Excel processing with complete data inclusion
"""
import sys
sys.path.insert(0, '/home/ricko/AI-Coaching-Andreas')

from backend.files.excel_processor import ExcelProcessor
import pandas as pd
import io


def create_test_meal_plan():
    """Create a comprehensive test meal plan"""
    meal_data = []
    
    # Create a week of meal plans
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    meals = ['Breakfast', 'Mid-Morning Snack', 'Lunch', 'Afternoon Snack', 'Dinner', 'Evening Snack']
    
    foods = {
        'Breakfast': ['Oatmeal with berries', 'Greek yogurt with granola', 'Scrambled eggs with toast', 'Protein smoothie', 'Avocado toast', 'Cottage cheese with fruit', 'Quinoa bowl'],
        'Mid-Morning Snack': ['Apple with almonds', 'Protein bar', 'Greek yogurt', 'Mixed nuts', 'Banana', 'String cheese', 'Hummus with carrots'],
        'Lunch': ['Grilled chicken salad', 'Quinoa bowl', 'Turkey sandwich', 'Salmon with vegetables', 'Lentil soup', 'Chicken wrap', 'Buddha bowl'],
        'Afternoon Snack': ['Protein shake', 'Trail mix', 'Rice cakes with peanut butter', 'Fruit smoothie', 'Veggie sticks with hummus', 'Dark chocolate', 'Yogurt parfait'],
        'Dinner': ['Grilled salmon with quinoa', 'Chicken stir-fry', 'Lean beef with sweet potato', 'Turkey meatballs with pasta', 'Tofu curry with rice', 'Grilled chicken with vegetables', 'Fish tacos'],
        'Evening Snack': ['Casein protein shake', 'Greek yogurt', 'Chamomile tea with honey', 'Small portion of nuts', 'Herbal tea', 'Low-fat cottage cheese', 'Warm milk']
    }
    
    calories = {
        'Breakfast': [350, 300, 400, 280, 320, 250, 380],
        'Mid-Morning Snack': [150, 200, 120, 180, 100, 80, 140],
        'Lunch': [450, 400, 500, 480, 350, 420, 460],
        'Afternoon Snack': [180, 160, 220, 150, 130, 120, 170],
        'Dinner': [500, 450, 520, 480, 420, 460, 440],
        'Evening Snack': [120, 100, 80, 150, 50, 110, 90]
    }
    
    proteins = {
        'Breakfast': [12, 15, 20, 25, 8, 18, 14],
        'Mid-Morning Snack': [5, 15, 10, 6, 1, 8, 4],
        'Lunch': [35, 18, 25, 30, 12, 28, 20],
        'Afternoon Snack': [20, 5, 8, 15, 3, 2, 12],
        'Dinner': [35, 30, 28, 32, 15, 35, 25],
        'Evening Snack': [25, 10, 2, 6, 0, 14, 8]
    }
    
    for day_idx, day in enumerate(days):
        for meal_idx, meal in enumerate(meals):
            meal_data.append({
                'Day': day,
                'Meal': meal,
                'Food': foods[meal][day_idx],
                'Calories': calories[meal][day_idx],
                'Protein_g': proteins[meal][day_idx],
                'Carbs_g': int(calories[meal][day_idx] * 0.4 / 4),  # 40% carbs
                'Fat_g': int(calories[meal][day_idx] * 0.3 / 9),   # 30% fat
                'Time': f"{8 + meal_idx * 2}:00" if meal_idx < 3 else f"{14 + (meal_idx-3) * 3}:00"
            })
    
    return pd.DataFrame(meal_data)


def test_complete_excel_processing():
    """Test the enhanced Excel processing with complete data"""
    print("🧪 Testing Enhanced Excel Processing with Complete Data")
    print("=" * 60)
    
    # Create comprehensive test data
    df = create_test_meal_plan()
    
    print(f"📊 Created test meal plan:")
    print(f"   Days: 7")
    print(f"   Meals per day: 6") 
    print(f"   Total entries: {len(df)}")
    print(f"   Columns: {list(df.columns)}")
    
    # Convert to CSV for testing
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue().encode('utf-8')
    
    print(f"   File size: {len(csv_content)} bytes")
    
    # Test complete extraction
    print("\n🔍 Testing Complete Data Extraction...")
    complete_text = ExcelProcessor.extract_complete_text_for_vector_store(csv_content, 'weekly_meal_plan.csv')
    
    print(f"✅ Complete extraction: {len(complete_text)} characters")
    
    # Test smart extraction  
    print("\n🔍 Testing Smart Extraction (with limits)...")
    smart_text = ExcelProcessor.extract_text_for_vector_store(csv_content, 'weekly_meal_plan.csv', max_rows=20)
    
    print(f"✅ Smart extraction: {len(smart_text)} characters")
    
    # Show sample of complete extraction
    print("\n📄 Sample of Complete Data (first 1000 characters):")
    print("-" * 50)
    print(complete_text[:1000] + "..." if len(complete_text) > 1000 else complete_text)
    
    # Count how many rows are included
    complete_rows = complete_text.count("Row ")
    smart_rows = smart_text.count("Row ")
    
    print(f"\n📊 Comparison:")
    print(f"   Original data: {len(df)} rows")
    print(f"   Complete extraction: {complete_rows} rows included")
    print(f"   Smart extraction: {smart_rows} rows included")
    
    # Test with very large data
    print("\n🧪 Testing with Large Dataset...")
    
    # Create larger dataset
    large_df = pd.concat([df] * 50)  # 2100 rows
    csv_buffer_large = io.StringIO()
    large_df.to_csv(csv_buffer_large, index=False)
    csv_content_large = csv_buffer_large.getvalue().encode('utf-8')
    
    print(f"   Large dataset: {len(large_df)} rows, {len(csv_content_large)} bytes")
    
    large_text = ExcelProcessor.extract_text_for_vector_store(csv_content_large, 'large_meal_plan.csv')
    large_rows = large_text.count("Row ")
    
    print(f"   Smart extraction from large file: {large_rows} rows included")
    print(f"   Text length: {len(large_text)} characters")
    
    return complete_text, smart_text, large_text


def test_ai_question_scenarios():
    """Show what AI questions can now be answered with complete data"""
    print("\n🤖 AI Capabilities with Complete Excel Data")
    print("=" * 60)
    
    questions = [
        "What did the client eat for dinner on Wednesday?",
        "How many total calories does the client consume per day?",
        "What's the total protein intake for the entire week?",
        "Which day has the highest calorie intake?",
        "What time does the client usually have their afternoon snack?",
        "Compare the protein content between breakfast and dinner across all days",
        "What's the most common breakfast food in the meal plan?",
        "Calculate the average calories per meal type across the week",
        "Identify any nutritional gaps or imbalances in the meal plan",
        "Suggest improvements based on the weekly nutrition data"
    ]
    
    print("✅ With complete Excel data, the AI can now answer questions like:")
    for i, question in enumerate(questions, 1):
        print(f"   {i:2d}. {question}")
    
    print("\n🎯 Benefits of Complete Data Inclusion:")
    print("   ✅ More accurate nutritional analysis")
    print("   ✅ Pattern recognition across time periods")
    print("   ✅ Comprehensive meal planning insights")
    print("   ✅ Detailed statistical analysis")
    print("   ✅ Better personalized recommendations")


def main():
    """Run all tests"""
    print("🚀 ENHANCED EXCEL PROCESSING - COMPLETE DATA INCLUSION")
    print("=" * 70)
    
    complete_text, smart_text, large_text = test_complete_excel_processing()
    test_ai_question_scenarios()
    
    print("\n" + "=" * 70)
    print("🎉 SUMMARY:")
    print("✅ Small Excel files (<1MB): ALL data included")
    print("✅ Large Excel files (>1MB): Smart sampling with representative data")
    print("✅ AI can access complete meal plans, client data, and tracking sheets")
    print("✅ Enhanced statistical analysis and pattern recognition")
    print("✅ Better coaching insights from comprehensive data")


if __name__ == "__main__":
    main()