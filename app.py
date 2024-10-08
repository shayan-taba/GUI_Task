import re
import os
import threading
import webview
import sys
import subprocess
import signal
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_file
import json
import pandas as pd
import random
from modules.utils import generate_test, get_statistics, get_category_stats, save_user_data, load_user_data, delete_user_data, headers
from modules.stats_util import create_category_performance_chart, create_progress_line_chart, create_correct_pie_chart
import uuid
from werkzeug.utils import secure_filename
import time

username_file = 'user_data/username.txt'
data_file = 'user_data/user_data.csv'
app = Flask(__name__)
app.secret_key = str(uuid.uuid4())  # Replace with a secure key

@app.route('/')
def index():
    username = read_username()  # Read the username from the file
    print(username,'\n\n\n')
    if 'user_data' in session:
        stats = get_statistics()
        return render_template('index.html', stats=stats, username=username)
    return render_template('index.html', username=username)

@app.route('/start_test', methods=['POST'])
def start_test():
    categories = request.form.getlist('categories')
    questions = generate_test(categories)
    session['questions'] = questions
    session['current_question'] = 0
    session['attempts'] = 0
    session['show_answer'] = 0
    session['score'] = 0
    return redirect(url_for('test'))

def print_session():
    session_data = {key: session[key] for key in session}
    return json.dumps(session_data, indent=1)

@app.route('/test', methods=['GET', 'POST'])
def test():
    print(print_session(),"PSPSPS") ### TESTING

    if 'questions' not in session:
        return redirect(url_for('index'))

    questions = session['questions']
    current_question = session.get('current_question', 0)
    correct_answer = questions[current_question]['answer']
    try:
        correct_answer_2 = questions[current_question]['answer_second']
    except:
        correct_answer_2 = correct_answer
    session['show_answer'] = 0
    feedback = None

    if request.method == 'POST':
        user_answer = request.form.get('answer')
        #save_user_data(questions[current_question], bool(user_answer == correct_answer), time.time())

        pattern = re.compile(r'^[0-9/]+$')
        if not(pattern.match(user_answer)) or (user_answer.isdigit() and int(user_answer)>100):
            return render_template('test.html', question=questions[current_question], show_answer=session.get('show_answer'), feedback= {"validate":'Please only enter integers from 0-100 or fractions'})
        
        if user_answer == correct_answer or user_answer == correct_answer_2:
            if session['attempts'] <= 1: # on the 2nd attempt, the answer was wrong again. answer is shown. result recorded as false.
                session['score'] += 1
                save_user_data(questions[current_question], bool((user_answer == correct_answer) | (user_answer == correct_answer_2)), time.time())
            session["attempts"] = 0
            session['current_question'] += 1
            if session['current_question'] >= len(questions): # all questions have been answered. test is finished. results page is rendered.
                session['current_question'] -= 1
                return redirect(url_for('results'))
            return redirect(url_for('test'))
        else:
            session['attempts'] += 1
            print('SASASA', session['attempts'])
            if session['attempts'] >= 2: # on the 2nd attempt, the answer was wrong again. answer is shown. result recorded as false.
                session['show_answer'] = correct_answer
                if session['attempts'] == 2:
                    save_user_data(questions[current_question], bool((user_answer == correct_answer) | (user_answer == correct_answer_2)), time.time())
            else: # on t he 1st attempt, the answer was wrong. a hint is given. no result recorded yet in csv.
                feedback = {"general":'That\'s not quite right',"hint": questions[current_question]['hint']}
            return render_template('test.html', question=questions[current_question], show_answer=session.get('show_answer'), feedback=feedback)

    return render_template('test.html', question=questions[current_question], show_answer=session.get('show_answer',0))

@app.route('/results')
def results():
    print(session["score"],"FICTION")
    if 'questions' not in session:
        return redirect(url_for('index'))
    
    questions = session["questions"]
    current_question = session["current_question"]
    
    #save_user_data(user_data)
    return render_template('test.html', question=questions[-1], show_answer=session.get('show_answer'), finished=True, score=session["score"], number_of_questions=len(questions))

@app.route('/view_data')
def view_data():
    data = load_user_data()
    data_available = True
    if len(data) == 0:
        data_available = False
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='s').apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
    table_html = data.to_html(classes='table table-striped', index=False)
    return render_template('view_data.html', data=table_html, data_available=data_available)

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

    if len(df) > 0:
        # Create charts
        category_performance_chart = create_category_performance_chart(df)
        correct_pie_chart = create_correct_pie_chart(df)
        progress_line_chart = create_progress_line_chart(df)

        # Render the results page with the charts
        return render_template('statistics.html',
                            category_chart=category_performance_chart,
                            pie_chart=correct_pie_chart,
                            line_chart=progress_line_chart,
                            data_available=True)
        #save_user_data(user_data)
        #return render_template('results.html')
        '''
        stats = get_category_stats()
        return render_template('results.html', stats=stats)
        '''
    return render_template('statistics.html', data_available=False)        

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

def read_username():
    """Retrieve the username from the specified text file."""
    if os.path.exists(username_file):
        with open(username_file, 'r') as file:
            return file.read().strip()
    return ''  # Default if not set

def save_username(username):
    """Save the username to the specified text file."""
    with open(username_file, 'w') as file:
        file.write(username)
        
@app.route('/save_username', methods=['POST'])
def save_username_route():
    data = request.get_json()
    username = data.get('username', '')
    save_username(username)
    return jsonify({'message': 'Username saved successfully!'})

# Run Flask app in a thread
def start_flask():
    app.run(port=8000)

def signal_handler(sig, frame):
    """Gracefully shut down the Flask server."""
    print('Shutting down Flask server...')
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

def toggle_fullscreen(window):
    # wait a few seconds before toggle fullscreen:
    time.sleep(0.5)

    window.toggle_fullscreen()
    
if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check for 'production' mode in the command-line arguments
    if len(sys.argv) > 1 and sys.argv[1] == 'production':
        flask_thread = threading.Thread(target=start_flask)
        flask_thread.daemon = True  # Ensure Flask exits when the main thread exits
        flask_thread.start()
        
        try:
            window = webview.create_window("Learning App for Kids", "http://127.0.0.1:8000/", fullscreen=True)
            webview.start(toggle_fullscreen, window)

        except Exception as e:
            print(f"Error occurred in webview: {e}")
            os._exit(0)  # Ensure proper exit on failure
        
        print("Webview closed, shutting down Flask...")
        os._exit(0)  # Forcefully close any remaining threads
    else:
        # Run in development mode with Flask's built-in server
        app.run(debug=True, port=8000)