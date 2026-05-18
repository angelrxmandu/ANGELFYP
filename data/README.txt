============================================================
  ZenFlow — Dataset Placement Instructions
============================================================

Place your Kaggle CSV files in THIS folder (data/).
The app will auto-detect them and use them for recommendations.
If the files are missing, built-in sample data is used instead.

------------------------------------------------------------
1. GYM EXERCISE DATASET
   Kaggle: https://www.kaggle.com/datasets/niharika41298/gym-exercise-data
   Save as: data/gym_exercises.csv
   Expected columns: Title, Type, BodyPart, Equipment, Level, Desc

------------------------------------------------------------
2. DAILY FOOD & NUTRITION DATASET
   Kaggle: https://www.kaggle.com/datasets/adilshamim8/daily-food-and-nutrition-dataset
   Save as: data/food_nutrition.csv
   Expected columns: Food_Name (or similar), Calories, Protein,
                     Carbohydrates, Fat, Meal_Type (optional)

------------------------------------------------------------
NOTE: Column names are normalised automatically, so minor
variations (e.g. "calories" vs "Calories") are handled.
If Meal_Type is absent, all foods are used for any meal slot.
============================================================
