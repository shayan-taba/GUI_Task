import json
import pandas as pd
import random
import os

headers = ['category', 'correct', 'timestamp']

def load_questions():
    with open('./questions.json') as f:
        return json.load(f)

def generate_test(categories):
    questions = load_questions()
    print(categories,'\n\n\n')
    filtered_questions = [q for q in questions if q['category'] in categories]
    return random.sample(filtered_questions, 20)

'''
def save_user_data(data):
    df = pd.DataFrame(data)
    df.to_csv('user_data/user_data.csv', mode='a', header=False, index=False)
'''

def load_user_data():
    return pd.read_csv('user_data/user_data.csv')

def delete_user_data():
    open('user_data/user_data.csv', 'w').close()
    file_path = 'user_data/user_data.csv'

    # Check if file exists and is not empty
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        # Create a DataFrame with headers if the file does not exist or is empty
        df = pd.DataFrame(columns=headers)
    
        new_data_df = pd.DataFrame(columns=headers)
    
        # Append new data
        df = pd.concat([df, new_data_df], ignore_index=True)
        
        # Save DataFrame to CSV
        df.to_csv(file_path, index=False)


def get_statistics():
    df = load_user_data()
    stats = df.describe()
    return stats

def get_category_stats():
    df = load_user_data()
    category_stats = df.groupby('category').mean()
    return category_stats

def save_user_data(question, correct, timestamp):
    file_path = 'user_data/user_data.csv'

    # Check if file exists and is not empty
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        # Create a DataFrame with headers if the file does not exist or is empty
        df = pd.DataFrame(columns=headers)
    else:
        # Read the existing data
        df = pd.read_csv(file_path)
    
    # Convert the new data to DataFrame
    new_data_df = pd.DataFrame([[question["category"], correct, timestamp]], columns=headers)
    
    # Append new data
    df = pd.concat([df, new_data_df], ignore_index=True)
    
    # Save DataFrame to CSV
    df.to_csv(file_path, index=False)
