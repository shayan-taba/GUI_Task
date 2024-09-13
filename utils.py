import json
import pandas as pd
import random

def load_questions():
    with open('./questions.json') as f:
        return json.load(f)

def generate_test(categories):
    questions = load_questions()
    filtered_questions = [q for q in questions if q['category'] in categories]
    return random.sample(filtered_questions, 5)

def save_user_data(data):
    df = pd.DataFrame(data)
    df.to_csv('user_data/user_data.csv', mode='a', header=False, index=False)

def load_user_data():
    return pd.read_csv('user_data/user_data.csv')

def delete_user_data():
    open('user_data/user_data.csv', 'w').close()

def get_statistics():
    df = load_user_data()
    stats = df.describe()
    return stats

def get_category_stats():
    df = load_user_data()
    category_stats = df.groupby('category').mean()
    return category_stats
