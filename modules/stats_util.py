import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, render_template, send_file
import io
import base64

matplotlib.use('Agg')


def create_category_performance_chart(df):
    """Create a bar chart for the performance of each category"""
    palette = {True: 'blue', False: 'red'}
    plt.figure(figsize=(10, 6))
    sns.countplot(x='category', hue='correct', data=df, palette=palette)
    plt.title('Correct vs Incorrect Answers by Category')
    plt.xlabel('Category')
    plt.ylabel('Count')
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode('utf-8')


def create_correct_pie_chart(df):
    """Create a pie chart for correct answers"""
    correct_counts = df['correct'].value_counts()

    try:
        plt.figure(figsize=(6, 6))
        plt.pie(correct_counts, labels=['Correct', 'Incorrect'],
                autopct='%1.1f%%', colors=['#66b3ff', '#ff6666'])
        plt.title('Correct vs Incorrect Answers')
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        return base64.b64encode(img.getvalue()).decode('utf-8')
    except Exception as e:
        # Likely caused by there not being at least one correct and incorrect
        # values
        return "error"


def create_progress_line_chart(df):
    """Create a line chart for progress over time"""

    df['date'] = pd.to_datetime(df['timestamp'], unit='s').dt.date

    df_summary = df.groupby(['date', 'category']).agg(
        {'correct': 'mean'}).reset_index()

    plt.figure(figsize=(10, 6))
    sns.barplot(x='date', y='correct', hue='category', data=df_summary)
    plt.title('Average Correct Answers by Date')
    plt.xlabel('Date')
    plt.ylabel('Average Correct (0-1)')
    plt.xticks(rotation=45)
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    base64_img = base64.b64encode(img.getvalue()).decode('utf-8')
    return base64_img
