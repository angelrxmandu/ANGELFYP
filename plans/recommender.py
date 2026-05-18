"""
Fitness and nutrition recommendation engine.

Loads exercise data from data/gym_exercises.csv (Kaggle: niharika41298/gym-exercise-data)
and food data from data/food_nutrition.csv (Kaggle: adilshamim8/daily-food-and-nutrition-dataset).
Falls back to built-in sample data if the CSV files are not present.
"""
import random
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Which exercise types match each goal
GOAL_EXERCISE_TYPES = {
    'muscle_growth':     ['Strength', 'Powerlifting'],
    'lose_fat':          ['Cardio', 'Strength'],
    'flexibility':       ['Stretching'],
    'strength_training': ['Strength', 'Powerlifting', 'Strongman'],
    'core':              ['Strength'],
    'running':           ['Cardio'],
    'daily_habits':      ['Strength', 'Cardio', 'Stretching'],
}

# Restrict body parts for specific goals (empty = no restriction)
GOAL_BODY_PARTS = {
    'core': ['Abdominals'],
}

# Number of exercises to pick per workout based on duration
DURATION_EXERCISE_COUNT = {15: 4, 30: 7, 60: 12}

# Indices into DAYS that are workout days (remaining are rest days)
WORKOUT_DAY_INDICES = {
    15: [0, 1, 2, 3, 4],       # Mon–Fri work, Sat–Sun rest
    30: [0, 1, 2, 3, 4],
    60: [0, 1, 2, 3, 4, 5],    # Mon–Sat work, Sun rest
}

# Caloric adjustment multiplier per goal
CALORIE_GOAL_FACTOR = {
    'muscle_growth':     1.10,
    'lose_fat':          0.85,
    'strength_training': 1.05,
    'running':           1.00,
    'flexibility':       1.00,
    'core':              1.00,
    'daily_habits':      1.00,
}

# Macro split (protein%, carbs%, fat%) per goal
MACRO_SPLITS = {
    'muscle_growth':     (0.30, 0.45, 0.25),
    'lose_fat':          (0.35, 0.35, 0.30),
    'flexibility':       (0.25, 0.50, 0.25),
    'strength_training': (0.30, 0.45, 0.25),
    'core':              (0.28, 0.47, 0.25),
    'running':           (0.25, 0.55, 0.20),
    'daily_habits':      (0.25, 0.50, 0.25),
}

# Activity multiplier for intensity 1–5 (Mifflin-St Jeor scale)
ACTIVITY_MULTIPLIER = {1: 1.20, 2: 1.375, 3: 1.55, 4: 1.725, 5: 1.90}

# How to split daily calories across meals
MEAL_CALORIE_RATIO = {'Breakfast': 0.30, 'Lunch': 0.35, 'Dinner': 0.35}

REST_DAY_TIPS = [
    'Rest day — hydrate well and let your muscles recover.',
    'Rest day — try a gentle walk or light stretching.',
    'Rest day — focus on sleep quality and recovery nutrition.',
    'Rest day — foam-roll tight areas and stay active lightly.',
]


# ---------------------------------------------------------------------------
# Calorie & macro helpers
# ---------------------------------------------------------------------------

def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    if gender == 'M':
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161


def _normalise_goals(goals) -> list:
    """Accept a single goal string or a list; always return a non-empty list."""
    if isinstance(goals, str):
        goals = [goals]
    return [g for g in goals if g] or ['daily_habits']


def calculate_daily_calories(weight_kg, height_cm, age, gender, intensity, goals) -> int:
    bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    tdee = bmr * ACTIVITY_MULTIPLIER.get(intensity, 1.55)
    goals = _normalise_goals(goals)
    avg_factor = sum(CALORIE_GOAL_FACTOR.get(g, 1.0) for g in goals) / len(goals)
    return max(1200, int(tdee * avg_factor))


def get_macros(goals, calories: int) -> dict:
    goals = _normalise_goals(goals)
    splits = [MACRO_SPLITS.get(g, (0.25, 0.50, 0.25)) for g in goals]
    p = sum(s[0] for s in splits) / len(splits)
    c = sum(s[1] for s in splits) / len(splits)
    f = sum(s[2] for s in splits) / len(splits)
    return {
        'protein_g': int(calories * p / 4),
        'carbs_g':   int(calories * c / 4),
        'fat_g':     int(calories * f / 9),
    }


# ---------------------------------------------------------------------------
# Dataset loading & normalisation
# ---------------------------------------------------------------------------

def _load_csv(*filenames) -> pd.DataFrame | None:
    for name in filenames:
        path = DATA_DIR / name
        if path.exists():
            try:
                df = pd.read_csv(path)
                df.columns = df.columns.str.strip()
                return df
            except Exception:
                continue
    return None


def load_exercises() -> pd.DataFrame:
    df = _load_csv('gym_exercises.csv', 'megaGymDataset.csv', 'exercises.csv')
    if df is not None:
        return _normalise_exercises(df)
    return _sample_exercises()


def load_foods() -> pd.DataFrame:
    df = _load_csv(
        'food_nutrition.csv', 'daily_food_nutrition.csv',
        'nutrition.csv', 'food.csv', 'diet.csv',
    )
    if df is not None:
        return _normalise_foods(df)
    return _sample_foods()


def _normalise_exercises(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for col in df.columns:
        low = col.lower()
        if low in ('title', 'name', 'exercise', 'exercise_name'):
            rename[col] = 'Title'
        elif low == 'type':
            rename[col] = 'Type'
        elif 'body' in low or 'part' in low or 'muscle' in low:
            rename[col] = 'BodyPart'
        elif 'equip' in low:
            rename[col] = 'Equipment'
        elif 'level' in low or 'diffic' in low:
            rename[col] = 'Level'
        elif 'desc' in low:
            rename[col] = 'Desc'
    df = df.rename(columns=rename)
    for col in ('Title', 'Type', 'BodyPart', 'Equipment', 'Level', 'Desc'):
        if col not in df.columns:
            df[col] = ''
    return df.dropna(subset=['Title'])


def _normalise_foods(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for col in df.columns:
        low = col.lower().replace(' ', '_').replace('(', '').replace(')', '')
        if any(k in low for k in ('food_name', 'food_item', 'item', 'name', 'meal_name')):
            rename[col] = 'Food_Name'
        elif any(k in low for k in ('calorie', 'energy', 'kcal')):
            rename[col] = 'Calories'
        elif 'protein' in low:
            rename[col] = 'Protein'
        elif any(k in low for k in ('carb', 'carbohydrate')):
            rename[col] = 'Carbohydrates'
        elif 'fat' in low and 'saturated' not in low:
            rename[col] = 'Fat'
        elif any(k in low for k in ('meal_type', 'meal', 'category', 'type')):
            rename[col] = 'Meal_Type'
    df = df.rename(columns=rename)

    if 'Meal_Type' not in df.columns:
        df['Meal_Type'] = 'Any'

    for col in ('Food_Name', 'Calories', 'Protein', 'Carbohydrates', 'Fat'):
        if col not in df.columns:
            df[col] = 0 if col != 'Food_Name' else 'Food Item'

    for col in ('Calories', 'Protein', 'Carbohydrates', 'Fat'):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df[df['Calories'] > 0].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Workout selection
# ---------------------------------------------------------------------------

def _pick_exercises(df: pd.DataFrame, goals, intensity: int, count: int) -> list:
    goals = _normalise_goals(goals)

    # Union of exercise types across all goals
    types = list({t for g in goals for t in GOAL_EXERCISE_TYPES.get(g, ['Strength'])})

    # Body-part restriction only if every selected goal restricts (intersection)
    bp_lists = [GOAL_BODY_PARTS.get(g, []) for g in goals]
    non_empty_bp = [bp for bp in bp_lists if bp]
    if non_empty_bp and len(non_empty_bp) == len(goals):
        body_parts = list(set.intersection(*[set(bp) for bp in non_empty_bp]))
    else:
        body_parts = []

    if intensity <= 2:
        levels = ['Beginner']
    elif intensity == 3:
        levels = ['Beginner', 'Intermediate']
    else:
        levels = ['Intermediate', 'Expert']

    filtered = df[df['Type'].isin(types)] if 'Type' in df.columns and not df.empty else df

    if body_parts and 'BodyPart' in filtered.columns:
        bp_filtered = filtered[filtered['BodyPart'].isin(body_parts)]
        if not bp_filtered.empty:
            filtered = bp_filtered

    if 'Level' in filtered.columns and not filtered.empty:
        lv_filtered = filtered[filtered['Level'].isin(levels)]
        if not lv_filtered.empty:
            filtered = lv_filtered

    if filtered.empty:
        filtered = df

    sample_size = min(count, len(filtered))
    selected = filtered.sample(sample_size, replace=False)

    results = []
    for _, row in selected.iterrows():
        ex_type = str(row.get('Type', 'Strength'))
        is_cardio = ex_type.lower() == 'cardio'
        results.append({
            'name':       str(row.get('Title', 'Exercise')),
            'type':       ex_type,
            'body_part':  str(row.get('BodyPart', 'Full Body')),
            'equipment':  str(row.get('Equipment', 'Body Only')),
            'level':      str(row.get('Level', 'Beginner')),
            'sets':       None if is_cardio else (3 if intensity >= 3 else 2),
            'reps':       None if is_cardio else (8 if goal == 'strength_training' else 12),
            'duration_min': (10 if count <= 4 else 5) if is_cardio else None,
        })
    return results


# ---------------------------------------------------------------------------
# Meal selection
# ---------------------------------------------------------------------------

def _pick_meal(df: pd.DataFrame, meal_name: str, target_cal: int) -> dict:
    lo, hi = target_cal * 0.70, target_cal * 1.30

    if 'Meal_Type' in df.columns:
        slot = df[
            df['Meal_Type'].str.lower().isin([meal_name.lower(), 'any', ''])
            & df['Calories'].between(lo, hi)
        ]
        if slot.empty:
            slot = df[df['Calories'].between(lo, hi)]
    else:
        slot = df[df['Calories'].between(lo, hi)]

    if slot.empty:
        # pick closest by absolute distance
        slot = df.copy()
        slot = slot.iloc[(slot['Calories'] - target_cal).abs().argsort()[:10]]

    row = slot.sample(1).iloc[0]
    return {
        'name':     str(row.get('Food_Name', 'Meal')),
        'calories': int(row['Calories']),
        'protein_g': round(float(row.get('Protein', 0)), 1),
        'carbs_g':   round(float(row.get('Carbohydrates', 0)), 1),
        'fat_g':     round(float(row.get('Fat', 0)), 1),
    }


# ---------------------------------------------------------------------------
# Main plan generator
# ---------------------------------------------------------------------------

def generate_weekly_plan(profile, goals, duration_minutes: int, intensity: int) -> tuple:
    """
    Returns (workout_plan, nutrition_plan, daily_calories, macros) as dicts
    keyed by day name ('Monday' … 'Sunday').
    goals may be a single string or a list of goal keys.
    """
    goals = _normalise_goals(goals)
    exercises_df = load_exercises()
    foods_df = load_foods()

    age = profile.age or 25
    gender = profile.gender or 'M'
    weight = profile.weight_kg or 70.0
    height = profile.height_cm or 170.0

    daily_calories = calculate_daily_calories(weight, height, age, gender, intensity, goals)
    macros = get_macros(goals, daily_calories)
    ex_count = DURATION_EXERCISE_COUNT.get(duration_minutes, 7)
    workout_indices = WORKOUT_DAY_INDICES.get(duration_minutes, [0, 1, 2, 3, 4])

    workout_plan = {}
    nutrition_plan = {}

    for idx, day in enumerate(DAYS):
        is_rest = idx not in workout_indices

        # --- Workout ---
        if is_rest:
            workout_plan[day] = {
                'is_rest_day': True,
                'exercises': [],
                'tip': random.choice(REST_DAY_TIPS),
            }
        else:
            workout_plan[day] = {
                'is_rest_day': False,
                'exercises': _pick_exercises(exercises_df, goals, intensity, ex_count),
                'duration_minutes': duration_minutes,
            }

        # --- Nutrition (every day including rest) ---
        meals = {}
        for meal_name, ratio in MEAL_CALORIE_RATIO.items():
            meals[meal_name] = _pick_meal(foods_df, meal_name, int(daily_calories * ratio))

        nutrition_plan[day] = {
            'meals': meals,
            'daily_calories': daily_calories,
            'macros': macros,
        }

    return workout_plan, nutrition_plan, daily_calories, macros


# ---------------------------------------------------------------------------
# Sample / fallback data
# ---------------------------------------------------------------------------

def _sample_exercises() -> pd.DataFrame:
    rows = [
        # name, type, bodypart, equipment, level
        ('Push-up',              'Strength',  'Chest',        'Body Only',  'Beginner'),
        ('Squat',                'Strength',  'Quadriceps',   'Body Only',  'Beginner'),
        ('Plank',                'Strength',  'Abdominals',   'Body Only',  'Beginner'),
        ('Lunges',               'Strength',  'Quadriceps',   'Body Only',  'Beginner'),
        ('Pull-up',              'Strength',  'Lats',         'Body Only',  'Intermediate'),
        ('Deadlift',             'Powerlifting','Hamstrings',  'Barbell',    'Intermediate'),
        ('Bench Press',          'Powerlifting','Chest',       'Barbell',    'Intermediate'),
        ('Shoulder Press',       'Strength',  'Shoulders',    'Dumbbell',   'Beginner'),
        ('Bicep Curl',           'Strength',  'Biceps',       'Dumbbell',   'Beginner'),
        ('Tricep Dip',           'Strength',  'Triceps',      'Body Only',  'Beginner'),
        ('Leg Press',            'Strength',  'Quadriceps',   'Machine',    'Beginner'),
        ('Hip Thrust',           'Strength',  'Glutes',       'Barbell',    'Beginner'),
        ('Russian Twist',        'Strength',  'Abdominals',   'Body Only',  'Beginner'),
        ('Crunches',             'Strength',  'Abdominals',   'Body Only',  'Beginner'),
        ('Bicycle Crunches',     'Strength',  'Abdominals',   'Body Only',  'Beginner'),
        ('Leg Raises',           'Strength',  'Abdominals',   'Body Only',  'Beginner'),
        ('V-ups',                'Strength',  'Abdominals',   'Body Only',  'Intermediate'),
        ('Side Plank',           'Strength',  'Abdominals',   'Body Only',  'Beginner'),
        ('Mountain Climbers',    'Cardio',    'Abdominals',   'Body Only',  'Intermediate'),
        ('Burpees',              'Cardio',    'Full Body',    'Body Only',  'Intermediate'),
        ('Jump Rope',            'Cardio',    'Calves',       'Body Only',  'Beginner'),
        ('Box Jump',             'Plyometrics','Quadriceps',  'Body Only',  'Intermediate'),
        ('Kettlebell Swing',     'Strength',  'Glutes',       'Kettlebells','Intermediate'),
        ('Running',              'Cardio',    'Full Body',    'Body Only',  'Beginner'),
        ('Cycling',              'Cardio',    'Quadriceps',   'Machine',    'Beginner'),
        ('Rowing Machine',       'Cardio',    'Lats',         'Machine',    'Beginner'),
        ('Elliptical',           'Cardio',    'Full Body',    'Machine',    'Beginner'),
        ('Battle Rope',          'Cardio',    'Full Body',    'Other',      'Intermediate'),
        ('Dumbbell Row',         'Strength',  'Lats',         'Dumbbell',   'Beginner'),
        ('Lat Pulldown',         'Strength',  'Lats',         'Machine',    'Beginner'),
        ('Seated Cable Row',     'Strength',  'Middle Back',  'Cable',      'Beginner'),
        ('Face Pull',            'Strength',  'Shoulders',    'Cable',      'Intermediate'),
        ('Arnold Press',         'Strength',  'Shoulders',    'Dumbbell',   'Intermediate'),
        ('Hammer Curl',          'Strength',  'Biceps',       'Dumbbell',   'Beginner'),
        ('Skull Crusher',        'Strength',  'Triceps',      'Barbell',    'Intermediate'),
        ('Calf Raise',           'Strength',  'Calves',       'Body Only',  'Beginner'),
        ('Glute Bridge',         'Strength',  'Glutes',       'Body Only',  'Beginner'),
        ('Good Morning',         'Strength',  'Hamstrings',   'Barbell',    'Intermediate'),
        ('Incline DB Press',     'Strength',  'Chest',        'Dumbbell',   'Intermediate'),
        ('Cable Fly',            'Strength',  'Chest',        'Cable',      'Intermediate'),
        ('Yoga Flow',            'Stretching','Full Body',    'Body Only',  'Beginner'),
        ('Cat-Cow Stretch',      'Stretching','Lower Back',   'Body Only',  'Beginner'),
        ('Hip Flexor Stretch',   'Stretching','Abdominals',   'Body Only',  'Beginner'),
        ('Hamstring Stretch',    'Stretching','Hamstrings',   'Body Only',  'Beginner'),
        ("Child's Pose",         'Stretching','Full Body',    'Body Only',  'Beginner'),
        ('Pigeon Pose',          'Stretching','Glutes',       'Body Only',  'Beginner'),
        ('Spinal Twist',         'Stretching','Lower Back',   'Body Only',  'Beginner'),
        ('Overhead Tricep Ext',  'Strength',  'Triceps',      'Dumbbell',   'Beginner'),
        ('Front Squat',          'Powerlifting','Quadriceps', 'Barbell',    'Intermediate'),
        ('Sumo Deadlift',        'Powerlifting','Glutes',     'Barbell',    'Intermediate'),
    ]
    cols = ['Title', 'Type', 'BodyPart', 'Equipment', 'Level']
    return pd.DataFrame(rows, columns=cols)


def _sample_foods() -> pd.DataFrame:
    rows = []
    # (name, calories, protein_g, carbs_g, fat_g, meal_type)
    breakfasts = [
        ('Oatmeal with Berries & Honey',       340, 11, 60,  7, 'Breakfast'),
        ('Greek Yogurt Parfait',                310, 21, 40,  8, 'Breakfast'),
        ('Scrambled Eggs on Whole Grain Toast', 370, 23, 34, 15, 'Breakfast'),
        ('Banana & Peanut Butter Smoothie',     390, 13, 55, 13, 'Breakfast'),
        ('Whole Grain Pancakes with Fruit',     420, 14, 70, 10, 'Breakfast'),
        ('Avocado Toast with Poached Egg',      360, 14, 36, 19, 'Breakfast'),
        ('Protein Omelette with Vegetables',    350, 29,  8, 22, 'Breakfast'),
        ('Chia Seed Pudding with Mango',        290, 10, 40, 11, 'Breakfast'),
        ('Whole Grain Cereal with Almond Milk', 300, 10, 52,  6, 'Breakfast'),
        ('Veggie Breakfast Burrito',            430, 18, 54, 15, 'Breakfast'),
        ('Smoked Salmon Bagel',                 410, 24, 44, 14, 'Breakfast'),
        ('Cottage Cheese with Pineapple',       280, 22, 30,  5, 'Breakfast'),
    ]
    lunches = [
        ('Grilled Chicken Salad',               420, 40, 20, 18, 'Lunch'),
        ('Quinoa Buddha Bowl',                  490, 18, 70, 14, 'Lunch'),
        ('Turkey & Avocado Sandwich',           460, 29, 50, 16, 'Lunch'),
        ('Lentil & Vegetable Soup',             380, 20, 58,  6, 'Lunch'),
        ('Tuna Salad Wrap',                     440, 34, 44, 13, 'Lunch'),
        ('Grilled Salmon with Brown Rice',      530, 42, 50, 17, 'Lunch'),
        ('Tofu & Vegetable Stir Fry',           390, 18, 52, 12, 'Lunch'),
        ('Chicken Burrito Bowl',                560, 38, 64, 16, 'Lunch'),
        ('Black Bean & Veggie Wrap',            420, 16, 62, 12, 'Lunch'),
        ('Shrimp Quinoa Bowl',                  470, 36, 54, 12, 'Lunch'),
        ('Greek Salad with Falafel',            440, 14, 52, 20, 'Lunch'),
        ('Chicken Caesar Salad',                450, 38, 20, 22, 'Lunch'),
    ]
    dinners = [
        ('Baked Salmon with Roasted Vegetables', 490, 42, 30, 22, 'Dinner'),
        ('Chicken Stir Fry with Noodles',         460, 38, 42, 15, 'Dinner'),
        ('Lean Beef & Broccoli with Rice',         530, 40, 48, 18, 'Dinner'),
        ('Whole Wheat Pasta with Tomato Sauce',    520, 20, 82, 12, 'Dinner'),
        ('Turkey Meatballs & Courgette Noodles',   440, 36, 24, 20, 'Dinner'),
        ('Grilled Tilapia with Asparagus',         400, 38, 18, 16, 'Dinner'),
        ('Chickpea Coconut Curry with Rice',       490, 16, 76, 14, 'Dinner'),
        ('Baked Chicken & Sweet Potato',           500, 42, 48, 13, 'Dinner'),
        ('Pork Tenderloin & Green Beans',          450, 42, 18, 20, 'Dinner'),
        ('Teriyaki Tofu Bowl',                     410, 22, 56, 13, 'Dinner'),
        ('Beef Taco Bowl',                         540, 36, 54, 20, 'Dinner'),
        ('Stuffed Bell Peppers with Quinoa',       430, 20, 58, 14, 'Dinner'),
    ]
    for row in breakfasts + lunches + dinners:
        rows.append({
            'Food_Name':      row[0],
            'Calories':       row[1],
            'Protein':        row[2],
            'Carbohydrates':  row[3],
            'Fat':            row[4],
            'Meal_Type':      row[5],
        })
    return pd.DataFrame(rows)
