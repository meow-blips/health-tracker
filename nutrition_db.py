"""
Built-in nutrition database for smart calorie detection.
Maps common food items to approximate nutritional values per standard serving.
"""

FOODS: list[dict] = [
    {"name": "Egg (boiled)", "serving": "1 large", "calories": 78, "protein_g": 6.3, "carbs_g": 0.6, "fat_g": 5.3},
    {"name": "Egg (scrambled)", "serving": "1 large", "calories": 91, "protein_g": 6.1, "carbs_g": 1.0, "fat_g": 6.7},
    {"name": "Egg (fried)", "serving": "1 large", "calories": 92, "protein_g": 6.3, "carbs_g": 0.4, "fat_g": 7.0},
    {"name": "Toast (white)", "serving": "1 slice", "calories": 79, "protein_g": 2.7, "carbs_g": 14.8, "fat_g": 1.0},
    {"name": "Toast (whole wheat)", "serving": "1 slice", "calories": 82, "protein_g": 4.0, "carbs_g": 13.8, "fat_g": 1.1},
    {"name": "Banana", "serving": "1 medium", "calories": 105, "protein_g": 1.3, "carbs_g": 27, "fat_g": 0.4},
    {"name": "Apple", "serving": "1 medium", "calories": 95, "protein_g": 0.5, "carbs_g": 25, "fat_g": 0.3},
    {"name": "Orange", "serving": "1 medium", "calories": 62, "protein_g": 1.2, "carbs_g": 15.4, "fat_g": 0.2},
    {"name": "Grapes", "serving": "1 cup", "calories": 104, "protein_g": 1.1, "carbs_g": 27, "fat_g": 0.2},
    {"name": "Strawberries", "serving": "1 cup", "calories": 49, "protein_g": 1.0, "carbs_g": 12, "fat_g": 0.5},
    {"name": "Blueberries", "serving": "1 cup", "calories": 84, "protein_g": 1.1, "carbs_g": 21, "fat_g": 0.5},
    {"name": "Rice (white, cooked)", "serving": "1 cup", "calories": 206, "protein_g": 4.3, "carbs_g": 45, "fat_g": 0.4},
    {"name": "Rice (brown, cooked)", "serving": "1 cup", "calories": 216, "protein_g": 5.0, "carbs_g": 45, "fat_g": 1.8},
    {"name": "Pasta (cooked)", "serving": "1 cup", "calories": 220, "protein_g": 8.1, "carbs_g": 43, "fat_g": 1.3},
    {"name": "Bread (white)", "serving": "1 slice", "calories": 67, "protein_g": 2.0, "carbs_g": 12.7, "fat_g": 0.8},
    {"name": "Bread (whole wheat)", "serving": "1 slice", "calories": 81, "protein_g": 3.6, "carbs_g": 13.8, "fat_g": 1.1},
    {"name": "Chicken breast (grilled)", "serving": "100g", "calories": 165, "protein_g": 31, "carbs_g": 0, "fat_g": 3.6},
    {"name": "Chicken thigh (grilled)", "serving": "100g", "calories": 209, "protein_g": 26, "carbs_g": 0, "fat_g": 10.9},
    {"name": "Salmon (grilled)", "serving": "100g", "calories": 208, "protein_g": 20, "carbs_g": 0, "fat_g": 13},
    {"name": "Tuna (canned)", "serving": "100g", "calories": 116, "protein_g": 26, "carbs_g": 0, "fat_g": 0.8},
    {"name": "Shrimp (cooked)", "serving": "100g", "calories": 99, "protein_g": 24, "carbs_g": 0.2, "fat_g": 0.3},
    {"name": "Beef (ground, lean)", "serving": "100g", "calories": 250, "protein_g": 26, "carbs_g": 0, "fat_g": 15},
    {"name": "Steak (sirloin)", "serving": "100g", "calories": 271, "protein_g": 26, "carbs_g": 0, "fat_g": 18},
    {"name": "Turkey breast", "serving": "100g", "calories": 135, "protein_g": 30, "carbs_g": 0, "fat_g": 1.0},
    {"name": "Paneer", "serving": "100g", "calories": 265, "protein_g": 18, "carbs_g": 1.2, "fat_g": 20.8},
    {"name": "Tofu (firm)", "serving": "100g", "calories": 144, "protein_g": 17, "carbs_g": 3, "fat_g": 8.7},
    {"name": "Milk (whole)", "serving": "1 cup", "calories": 149, "protein_g": 8, "carbs_g": 12, "fat_g": 8},
    {"name": "Milk (skim)", "serving": "1 cup", "calories": 83, "protein_g": 8.3, "carbs_g": 12.2, "fat_g": 0.2},
    {"name": "Yogurt (plain)", "serving": "1 cup", "calories": 149, "protein_g": 8.5, "carbs_g": 11.4, "fat_g": 8},
    {"name": "Greek yogurt", "serving": "1 cup", "calories": 100, "protein_g": 17, "carbs_g": 6, "fat_g": 0.7},
    {"name": "Cheese (cheddar)", "serving": "1 oz (28g)", "calories": 113, "protein_g": 7, "carbs_g": 0.4, "fat_g": 9.3},
    {"name": "Butter", "serving": "1 tbsp", "calories": 102, "protein_g": 0.1, "carbs_g": 0, "fat_g": 11.5},
    {"name": "Olive oil", "serving": "1 tbsp", "calories": 119, "protein_g": 0, "carbs_g": 0, "fat_g": 13.5},
    {"name": "Avocado", "serving": "1 medium", "calories": 240, "protein_g": 3, "carbs_g": 13, "fat_g": 22},
    {"name": "Almonds", "serving": "1 oz (28g)", "calories": 164, "protein_g": 6, "carbs_g": 6, "fat_g": 14},
    {"name": "Peanut butter", "serving": "2 tbsp", "calories": 188, "protein_g": 8, "carbs_g": 6, "fat_g": 16},
    {"name": "Oatmeal (cooked)", "serving": "1 cup", "calories": 154, "protein_g": 6, "carbs_g": 27, "fat_g": 2.6},
    {"name": "Cereal (corn flakes)", "serving": "1 cup", "calories": 101, "protein_g": 2, "carbs_g": 24, "fat_g": 0.2},
    {"name": "Potato (baked)", "serving": "1 medium", "calories": 161, "protein_g": 4.3, "carbs_g": 37, "fat_g": 0.2},
    {"name": "Sweet potato", "serving": "1 medium", "calories": 103, "protein_g": 2.3, "carbs_g": 24, "fat_g": 0.1},
    {"name": "Broccoli (cooked)", "serving": "1 cup", "calories": 55, "protein_g": 3.7, "carbs_g": 11, "fat_g": 0.6},
    {"name": "Spinach (raw)", "serving": "1 cup", "calories": 7, "protein_g": 0.9, "carbs_g": 1.1, "fat_g": 0.1},
    {"name": "Carrot", "serving": "1 medium", "calories": 25, "protein_g": 0.6, "carbs_g": 6, "fat_g": 0.1},
    {"name": "Tomato", "serving": "1 medium", "calories": 22, "protein_g": 1.1, "carbs_g": 4.8, "fat_g": 0.2},
    {"name": "Cucumber", "serving": "1 cup sliced", "calories": 16, "protein_g": 0.7, "carbs_g": 3.1, "fat_g": 0.2},
    {"name": "Lentils (cooked)", "serving": "1 cup", "calories": 230, "protein_g": 18, "carbs_g": 40, "fat_g": 0.8},
    {"name": "Chickpeas (cooked)", "serving": "1 cup", "calories": 269, "protein_g": 14.5, "carbs_g": 45, "fat_g": 4.2},
    {"name": "Black beans (cooked)", "serving": "1 cup", "calories": 227, "protein_g": 15, "carbs_g": 41, "fat_g": 0.9},
    {"name": "Dal (cooked)", "serving": "1 cup", "calories": 198, "protein_g": 13, "carbs_g": 34, "fat_g": 1.0},
    {"name": "Roti / Chapati", "serving": "1 piece", "calories": 104, "protein_g": 3.0, "carbs_g": 18, "fat_g": 3.0},
    {"name": "Naan", "serving": "1 piece", "calories": 262, "protein_g": 8.7, "carbs_g": 45, "fat_g": 5.1},
    {"name": "Pizza (cheese)", "serving": "1 slice", "calories": 272, "protein_g": 12, "carbs_g": 34, "fat_g": 10},
    {"name": "Burger (beef)", "serving": "1 regular", "calories": 354, "protein_g": 20, "carbs_g": 29, "fat_g": 17},
    {"name": "French fries", "serving": "medium", "calories": 365, "protein_g": 4, "carbs_g": 44, "fat_g": 17},
    {"name": "Sandwich (turkey)", "serving": "1 whole", "calories": 320, "protein_g": 21, "carbs_g": 36, "fat_g": 10},
    {"name": "Salad (garden)", "serving": "1 bowl", "calories": 35, "protein_g": 2, "carbs_g": 7, "fat_g": 0.3},
    {"name": "Soup (chicken noodle)", "serving": "1 cup", "calories": 62, "protein_g": 3.2, "carbs_g": 7.3, "fat_g": 2.4},
    {"name": "Coffee (black)", "serving": "1 cup", "calories": 2, "protein_g": 0.3, "carbs_g": 0, "fat_g": 0},
    {"name": "Coffee (with milk)", "serving": "1 cup", "calories": 30, "protein_g": 1.5, "carbs_g": 2, "fat_g": 1.5},
    {"name": "Latte", "serving": "12 oz", "calories": 150, "protein_g": 10, "carbs_g": 15, "fat_g": 6},
    {"name": "Tea (plain)", "serving": "1 cup", "calories": 2, "protein_g": 0, "carbs_g": 0.5, "fat_g": 0},
    {"name": "Chai (with milk)", "serving": "1 cup", "calories": 120, "protein_g": 4, "carbs_g": 15, "fat_g": 4},
    {"name": "Orange juice", "serving": "1 cup", "calories": 112, "protein_g": 1.7, "carbs_g": 26, "fat_g": 0.5},
    {"name": "Soda (cola)", "serving": "12 oz", "calories": 140, "protein_g": 0, "carbs_g": 39, "fat_g": 0},
    {"name": "Water", "serving": "1 glass", "calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0},
    {"name": "Protein shake", "serving": "1 scoop + water", "calories": 120, "protein_g": 24, "carbs_g": 3, "fat_g": 1.5},
    {"name": "Granola bar", "serving": "1 bar", "calories": 190, "protein_g": 3, "carbs_g": 29, "fat_g": 7},
    {"name": "Dark chocolate", "serving": "1 oz (28g)", "calories": 170, "protein_g": 2.2, "carbs_g": 13, "fat_g": 12},
    {"name": "Ice cream (vanilla)", "serving": "1/2 cup", "calories": 137, "protein_g": 2.3, "carbs_g": 16, "fat_g": 7.3},
    {"name": "Cookie (chocolate chip)", "serving": "1 medium", "calories": 78, "protein_g": 0.9, "carbs_g": 9.3, "fat_g": 4.5},
    {"name": "Dosa", "serving": "1 piece", "calories": 133, "protein_g": 3.9, "carbs_g": 18.8, "fat_g": 5.2},
    {"name": "Idli", "serving": "1 piece", "calories": 39, "protein_g": 1.0, "carbs_g": 7.9, "fat_g": 0.2},
    {"name": "Samosa", "serving": "1 piece", "calories": 262, "protein_g": 3.5, "carbs_g": 24, "fat_g": 17},
    {"name": "Biryani (chicken)", "serving": "1 cup", "calories": 290, "protein_g": 16, "carbs_g": 38, "fat_g": 8},
    {"name": "Butter chicken", "serving": "1 cup", "calories": 438, "protein_g": 30, "carbs_g": 12, "fat_g": 28},
    {"name": "Palak paneer", "serving": "1 cup", "calories": 330, "protein_g": 16, "carbs_g": 10, "fat_g": 25},
    {"name": "Fried rice", "serving": "1 cup", "calories": 238, "protein_g": 5, "carbs_g": 34, "fat_g": 9},
    {"name": "Poha", "serving": "1 cup", "calories": 244, "protein_g": 4.5, "carbs_g": 33, "fat_g": 10},
    {"name": "Upma", "serving": "1 cup", "calories": 210, "protein_g": 5, "carbs_g": 30, "fat_g": 7.5},
]


def search_foods(query: str, limit: int = 10) -> list[dict]:
    if not query or len(query) < 2:
        return []
    terms = query.lower().split()
    results = []
    for food in FOODS:
        name_lower = food["name"].lower()
        score = sum(1 for term in terms if term in name_lower)
        if score > 0:
            results.append((score, food))
    results.sort(key=lambda x: (-x[0], x[1]["name"]))
    return [r[1] for r in results[:limit]]
