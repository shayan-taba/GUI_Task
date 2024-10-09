import json
import pandas as pd
import random
import os

headers = ['category', 'correct', 'timestamp'] # Headers of CSV file

def load_questions():
    """ Loads the list of available questions """
    with open('./static/assets/questions.json') as f:
        return json.load(f)

def generate_test(categories):
    """ Based on chosen categories, generates a test by randomly choosing a certain amount of questions """
    questions = load_questions()
    print(categories,'\n\n\n')
    filtered_questions = [q for q in questions if q['category'] in categories]
    return random.sample(filtered_questions, 5)

def load_user_data():
    """ Uses Pandas read the CSV """
    return pd.read_csv('user_data/user_data.csv')

def delete_user_data():
    """ Deletes the USERNAME data and CSV data """
    file_path = 'user_data/user_data.csv'
    open(file_path, 'w').close() # Deletes CSV
    
    open('user_data/username.txt', 'w').close() # Deletes stored username

    # Check if file exists and is not empty
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        # Create a DataFrame with headers if the file does not exist or is empty
        df = pd.DataFrame(columns=headers)
    
        new_data_df = pd.DataFrame(columns=headers)
    
        # Append new data
        df = pd.concat([df, new_data_df], ignore_index=True)
        
        # Save DataFrame to CSV as a blank template
        df.to_csv(file_path, index=False)

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
