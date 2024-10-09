import mimetypes
import re
import os
import threading
import webview
import sys
import signal
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_file
import json
import pandas as pd
from modules.utils import generate_test, get_statistics, get_category_stats, save_user_data, load_user_data, delete_user_data, headers
from modules.stats_util import create_category_performance_chart, create_progress_line_chart, create_correct_pie_chart
import uuid
from werkzeug.utils import secure_filename
import time

username_file = 'user_data/username.txt' # Where the username is stored
data_file = 'user_data/user_data.csv' # Where the CSV of results are stored
app = Flask(__name__)
app.secret_key = str(uuid.uuid4())

@app.route('/')  # Home page
def index():
    """ Home page where user navigates to all other pages and generates test """
    username = read_username() # Reads the username from the file
    return render_template('index.html', username=username) # Home page with the stored username

@app.route('/start_test', methods=['POST'])
def start_test():
    """ Generates a test based on selected categories. """
    categories = request.form.getlist('categories') # Get the selected categories from the POST form that redirected here
    questions = generate_test(categories) # Generates the test by the categories in the utilis.py module
    session['questions'] = questions # Saves the generated question in the temporary data to be later used by "/test"
    session['current_question'] = 0 # Resets all variables to 0 at start of test
    session['attempts'] = 0
    session['show_answer'] = 0
    session['score'] = 0
    return redirect(url_for('test')) # After test has been created, start the test

def print_session():
    """ Only for development and debugging purposes. """
    session_data = {key: session[key] for key in session}
    return json.dumps(session_data, indent=1)

@app.route('/test', methods=['GET', 'POST']) # The actual questions of the test themselves
def test():
    """ Iterates through questions, handles question validation, handles checking if answer is correct, handles delivery of 'hints', 'answers'."""
    if 'questions' not in session: # Error handling
        # If the user misnavigates to this page, but no test was generated it redirects back to home.
        return redirect(url_for('index'))

    questions = session['questions'] # Get back the questions previously generated from /start_test
    current_question = session.get('current_question', 0) # Get current_question index (an integer the keeps track of the questions answered)
    # If "current_question" can't be found, it assumed the default is 0 and the test has just been generated.
    
    correct_answer = questions[current_question]['answer'] # The answer of the current question being answered.
    try:  # If there is a 2nd correct answer (due to fraction simplification), retrieve it
        correct_answer_2 = questions[current_question]['answer_second']
    except:  # Occurs when there is no 2nd answer. This makes the variable accordingly reduntant by making it equal to answer.
        correct_answer_2 = correct_answer
    session['show_answer'] = 0  # Once a new question is displayed on 1st attempt, the answer musn't be shown, likewise with the feeback.
    feedback = None

    if request.method == 'POST': # Only occurs if a POST request redirects, i.e., it is not the 1st question
        user_answer = request.form.get('answer') # User's attempted answer

        pattern = re.compile(r'^[0-9/]+$')  # Regex that validates the data to check if its "NORMAL". Only allows integers and the "/" sign.
        if not(pattern.match(user_answer)) or (user_answer.isdigit() and int(user_answer)>100): # If its not NORMAL data that is not between 0-100 or a fraction
            return render_template('test.html', question=questions[current_question], show_answer=session.get('show_answer'), feedback= {"validate":'Please only enter integers from 0-100 or fractions'})
            # This displays the previous question, doesnt count the previous attempt as an attempt, and alerts the user that they entered ABNORMAL data.
            
        if user_answer == correct_answer or user_answer == correct_answer_2:  # If user was correct.
            if session['attempts'] <= 1: # Only on the 1st or 2nd attempt. 
                session['score'] += 1 # Only count as "correct" in CSV on 1st, 2nd, but not the 3rd attempt
                save_user_data(questions[current_question], bool((user_answer == correct_answer) | (user_answer == correct_answer_2)), time.time())
                # Add to CSV
                
            session["attempts"] = 0 # Resets this counter as this question is finished and the next one is to be shown
            session['current_question'] += 1 # Counter increments as its the next question.
            if session['current_question'] >= len(questions): # All questions have been answered. Test is finished. Results page is rendered.
                session['current_question'] -= 1 # Accounts for the fact that after a correct attempt the counter is incremented by one too much.
                return redirect(url_for('results')) # Results page is rendered.
            return redirect(url_for('test')) # This only occurs if the prior if statement didn't occur, i.e., the user did enter the correct answer, but it was 
            # (continuing from previous line) given by hints beyond the 3rd attempt. CSV has already been recorded as false answe. No further CSV actions required.
        else: # Answer was false
            session['attempts'] += 1 # increment attempt counter
            if session['attempts'] >= 2: # on the 2nd or beyond attempt, the answer was wrong again. Answer is shown. Result recorded as false in CSV.
                session['show_answer'] = correct_answer
                if session['attempts'] == 2:
                    save_user_data(questions[current_question], bool((user_answer == correct_answer) | (user_answer == correct_answer_2)), time.time())
            else: # On the 1st attempt, the answer was wrong. A hint is given, but not the answer. No result recorded yet in csv.
                feedback = {"general":'That\'s not quite right',"hint": questions[current_question]['hint']}
            return render_template('test.html', question=questions[current_question], show_answer=session.get('show_answer'), feedback=feedback) # Gives user another attempt

    return render_template('test.html', question=questions[current_question], show_answer=session.get('show_answer',0)) # This only happens if no other "return" occured, i.e., 1st question and no attempts.

@app.route('/results') # Displayed if all questions have been answered.
def results():
    """ Counts amount of correct answers and displays it once test finished. """
    if 'questions' not in session:
        return redirect(url_for('index')) # Error handling, redirects to home. This happens if user misnavigates to this page without completing question. 
    
    questions = session["questions"]
    
    return render_template('test.html', question=questions[-1], show_answer=session.get('show_answer'), finished=True, score=session["score"], number_of_questions=len(questions))
    # Display popup of the SCORE.

@app.route('/view_data') # 
def view_data():
    """ Turns data into table for the user to view. Also provides various options for the user like deleting data. """
    data = load_user_data() # Gets CSV
    data_available = True
    if len(data) == 0:
        data_available = False # If no data yet in CSV, this will be passed onto Jinja2 template.
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='s').apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S')) # Convert all timestamps to human friendly.
    table_html = data.to_html(classes='table table-striped', index=False) # Converts CSV to HTML table.
    return render_template('view_data.html', data=table_html, data_available=data_available)

@app.route('/delete_data', methods=['POST']) # If user wishes to delete data
def delete_data():
    """ Deletes the username and CSV and go back home """
    delete_user_data() 
    return redirect(url_for('index')) 
    
@app.route('/statistics')
def statistics():
    """ statsitics page uses modules ad libraries to create data into charts that are shown """
    df = load_user_data() # get CSV

    if len(df) > 0: # If there is data
        # Create charts. For more details refer to ./modules/stats_util.py
        category_performance_chart = create_category_performance_chart(df)
        correct_pie_chart = create_correct_pie_chart(df)
        progress_line_chart = create_progress_line_chart(df)

        # Render the results page with the charts
        return render_template('statistics.html',
                            category_chart=category_performance_chart,
                            pie_chart=correct_pie_chart,
                            line_chart=progress_line_chart,
                            data_available=True)
        
    return render_template('statistics.html', data_available=False) # Only runs if there was no data in CSV.       

app.config['UPLOAD_FOLDER'] = 'uploads/' # Folder directory for CSV uploads
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

def allowed_file(filename): # Checks if filetype is valid
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/import_csv', methods=['POST']) # If user wishes to import data.
def import_csv():
    """ import prior version of csv data to be kept and used by the app. """
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    
    # Check if the filename is empty
    if file.filename == '':
        return redirect(request.url)
    
    # Check if the file extension is allowed
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Check the MIME type of the file to ensure it's a CSV as a 2nd check.
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type != 'text/csv':
            return render_template('index.html', CSV_ERROR=True, username=read_username(), error="Invalid file type. Please upload a CSV.")
            # Goes back to home page and tells user of the issue (incorrect file formatting)
        
        # Save the file
        file.save(filepath)
        
        # Process the CSV (you already have this part)
        df = pd.read_csv(filepath)
        df.dropna(how='all', inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
        
        # Validate DataFrame columns and data
        if 'category' in df.columns and 'correct' in df.columns and 'timestamp' in df.columns:
            df.to_csv(data_file, mode='w', header=headers, index=False) # Correct Formatting
        else:
            return render_template('index.html', CSV_ERROR=True, username=read_username())
            # Incorrect formatting as CSV is wrongly formatted.
        
        return redirect(url_for('index')) # Go back to home page after upload
    else:
        return render_template('index.html', CSV_ERROR=True, username=read_username(), error="Invalid file type. Please upload a CSV.")
        # Goes back to home page and tells user of the issue (incorrect file formatting)

@app.route('/export_csv') 
def export_csv():
    """ exports in downloads as csv """
    if os.path.exists(data_file): # If the CSV file exists
        return send_file(data_file, as_attachment=True) # Download it
    else:
        return "No data available to export"

def read_username():
    """Retrieve the username from the specified text file."""
    if os.path.exists(username_file):
        with open(username_file, 'r') as file:
            return file.read().strip()
    return ''  # Default if not set

def save_username(username):
    """Save the username to the specified text file function."""
    with open(username_file, 'w') as file:
        file.write(username)
        
@app.route('/save_username', methods=['POST'])
def save_username_route():
    """Save the username to the specified text file."""
    data = request.get_json()
    username = data.get('username', '')
    save_username(username)
    return jsonify({'message': 'Username saved successfully!'})

# Run Flask app in a thread
def start_flask():
    app.run(port=8000)

def signal_handler(sig, frame): 
    """Shut down the Flask server in a way to avoid crashing."""
    print('Shutting down Flask server...')
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

def toggle_fullscreen(window):
    """wait a few seconds before toggle fullscreen"""
    time.sleep(0.5)

    window.toggle_fullscreen()
    
if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check for 'production' mode in the command-line arguments
    if len(sys.argv) > 1 and sys.argv[1] == 'production' or True: # This always run and is reduntant. It is only here for development purposes so it can be switched off for debugging.
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