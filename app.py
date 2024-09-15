import os
import threading
import webview  # Import PyWebview
import sys
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_file
import json
import pandas as pd
import random
from utils import generate_test, get_statistics, get_category_stats, save_user_data, load_user_data, delete_user_data, headers
from stats_util import create_category_performance_chart, create_progress_line_chart, create_correct_pie_chart
import uuid
from werkzeug.utils import secure_filename
import time

data_file = 'user_data/user_data.csv'
app = Flask(__name__)
app.secret_key = str(uuid.uuid4())  # Replace with a secure key

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

def print_session():
    session_data = {key: session[key] for key in session}
    return json.dumps(session_data, indent=1)

@app.route('/test', methods=['GET', 'POST'])
def test():
    print(print_session()) ### TESTING

    if 'questions' not in session:
        return redirect(url_for('index'))
    
    questions = session['questions']
    current_question = session.get('current_question', 0)
    correct_answer = questions[current_question]['answer']
    session['show_answer'] = 0
    feedback = None
    
    if request.method == 'POST':
        user_answer = request.form.get('answer')
        save_user_data(questions[current_question], bool(user_answer == correct_answer), time.time())
        
        if user_answer == correct_answer:
            session["attempts"] = 0
            session['current_question'] += 1
            if session['current_question'] >= len(questions):
                return redirect(url_for('results'))
            return redirect(url_for('test'))
        else:
            session['attempts'] += 1
            if session['attempts'] >= 2:
                session['show_answer'] = correct_answer
            else:
                feedback = {"general":'That\'s not quite right',"hint": questions[current_question]['hint']}
            return render_template('test.html', question=questions[current_question], show_answer=session.get('show_answer'), feedback=feedback)

    return render_template('test.html', question=questions[current_question], show_answer=session.get('show_answer',0))

@app.route('/results')
def results():
    if 'questions' not in session:
        return redirect(url_for('index'))

    questions = session['questions']
    user_data = {
        'questions': questions,
        'attempts': session['attempts']
    }
    #save_user_data(user_data)
    return render_template('results.html')

@app.route('/view_data')
def view_data():
    data = load_user_data()
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='s').apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
    table_html = data.to_html(classes='table table-striped', index=False)
    return render_template('view_data.html', data=table_html)

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
    #if 'questions' not in session:
        #return redirect(url_for('index'))

    df = load_user_data()

    # Create charts
    category_performance_chart = create_category_performance_chart(df)
    correct_pie_chart = create_correct_pie_chart(df)
    progress_line_chart = create_progress_line_chart(df)
    
    print(category_performance_chart)
    print('mashallah')

    # Render the results page with the charts
    return render_template('statistics.html',
                           category_chart=category_performance_chart,
                           pie_chart=correct_pie_chart,
                           line_chart=progress_line_chart)
    #save_user_data(user_data)
    #return render_template('results.html')
    '''
    stats = get_category_stats()
    return render_template('results.html', stats=stats)
    '''

app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/import_csv', methods=['POST'])
def import_csv():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read CSV file into DataFrame
        df = pd.read_csv(filepath)
        
        # Clean DataFrame: drop empty rows and columns
        df.dropna(how='all', inplace=True)  # Drop rows where all elements are NaN
        df.dropna(axis=1, how='all', inplace=True)  # Drop columns where all elements are NaN
        
        # Validate DataFrame columns and data
        if 'category' in df.columns and 'correct' in df.columns and 'timestamp' in df.columns:
            df.to_csv(data_file, mode='w', header=headers, index=False)
        else:
            return "CSV file format is incorrect. Please ensure it has 'category', 'correct', and 'timestamp' columns."
        
        return redirect(url_for('index'))

@app.route('/export_csv')
def export_csv():
    if os.path.exists(data_file):
        return send_file(data_file, as_attachment=True)
    else:
        return "No data available to export"

# Run Flask app in a thread
def start_flask():
    app.run(port=8000)
    
if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    # Check for 'production' mode in the command-line arguments
    if len(sys.argv) > 1 and sys.argv[1] == 'production':
        # Run in production mode with PyWebview
        threading.Thread(target=start_flask).start()  # Start Flask in a separate thread
        webview.create_window("Learning App for Kids", "http://127.0.0.1:8000/")  # Open the app in a PyWebview window
        webview.start()
    else:
        # Run in development mode with Flask's built-in server
        app.run(debug=True, port=8000)

