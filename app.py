from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import json
import pandas as pd
import random
from utils import generate_test, get_statistics, get_category_stats, save_user_data, load_user_data, delete_user_data

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

@app.route('/')
def index():
    if 'user_data' in session:
        stats = get_statistics()
        return render_template('index.html', stats=stats)
    return render_template('index.html')

@app.route('/start_test', methods=['POST'])
def start_test():
    categories = request.form.getlist('categories')
    questions = generate_test(categories)
    session['questions'] = questions
    session['current_question'] = 0
    session['attempts'] = 0
    return redirect(url_for('test'))

@app.route('/test', methods=['GET', 'POST'])
def test():
    if 'questions' not in session:
        return redirect(url_for('index'))
    
    questions = session['questions']
    current_question = session.get('current_question', 0)

    if request.method == 'POST':
        user_answer = request.form.get('answer')
        correct_answer = questions[current_question]['answer']
        if user_answer == correct_answer:
            session['current_question'] += 1
            if session['current_question'] >= len(questions):
                return redirect(url_for('results'))
            return redirect(url_for('test'))
        else:
            session['attempts'] += 1
            if session['attempts'] >= 2:
                session['show_answer'] = correct_answer
            return render_template('test.html', question=questions[current_question], show_answer=session.get('show_answer'))

    return render_template('test.html', question=questions[current_question], show_answer=session.get('show_answer'))

@app.route('/results')
def results():
    if 'questions' not in session:
        return redirect(url_for('index'))

    questions = session['questions']
    user_data = {
        'questions': questions,
        'attempts': session['attempts']
    }
    save_user_data(user_data)
    return render_template('results.html')

@app.route('/view_data')
def view_data():
    data = load_user_data()
    return render_template('view_data.html', data=data)

@app.route('/delete_data', methods=['POST'])
def delete_data():
    delete_user_data()
    return redirect(url_for('index'))

@app.route('/generate_random_test')
def generate_random_test():
    categories = request.args.getlist('categories')
    questions = generate_test(categories)
    return jsonify(questions)

@app.route('/statistics')
def statistics():
    stats = get_category_stats()
    return render_template('results.html', stats=stats)

if __name__ == '__main__':
    app.run(debug=True)
