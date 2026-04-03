from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pandas as pd
import os
from analysis import process_full_analysis # Import our new module

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# MySQL Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'rootuser1', # CHANGE THIS
    'database': 'fit'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def login_required(f):
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# --- ROUTES ---

@app.route('/')
def welcome():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('welcome.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        age = request.form['age']
        gender = request.form['gender']
        password = generate_password_hash(request.form['password'])

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            flash('Username exists', 'error')
            return render_template('register.html')

        cursor.execute(
            'INSERT INTO users (username, email, age, gender, password) VALUES (%s, %s, %s, %s, %s)',
            (username, email, age, gender, password)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash('Registered! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('welcome'))

@app.route('/home')
@login_required
def home():
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM health_data WHERE username = %s ORDER BY entry_time DESC LIMIT 1', (username,))
    latest = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('home.html', user={'username': username}, latest=latest or {})

# --- NEW: UPLOAD FEATURE (Milestone 4 Logic) ---
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_data():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        try:
            # Read file
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.filename.endswith('.json'):
                df = pd.read_json(file)
            else:
                flash('Unsupported format. Use CSV or JSON.', 'error')
                return redirect(request.url)

            # Process using our new analysis module
            df = process_full_analysis(df)

            # Save to DB
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            count = 0
            for _, row in df.iterrows():
                # Find date column dynamically
                date_val = row.get('entry_time') or row.get('ds') or row.get('timestamp') or datetime.now()

                # Find metric columns dynamically
                hr = row.get('heart_rate') or row.get('heart_rate_bpm') or 0
                steps = row.get('steps') or 0
                sleep = row.get('sleep') or 0
                status = row.get('severity', 'Healthy') # Use calculated severity

                cursor.execute(
                    """INSERT INTO health_data (username, heart_rate, steps, sleep, status, entry_time)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (session['username'], int(hr), int(steps), float(sleep), status, date_val)
                )
                count += 1

            conn.commit()
            cursor.close()
            conn.close()
            flash(f'Successfully imported {count} records!', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')

    return render_template('upload.html')

@app.route('/data_entry', methods=['GET', 'POST'])
@login_required
def data_entry():
    if request.method == 'POST':
        username = session['username']
        hr = int(request.form['heartRate'])
        steps = int(request.form['steps'])
        sleep = float(request.form['sleep'])
        entry_time = datetime.strptime(request.form['time'], '%Y-%m-%dT%H:%M')

        # Run basic analysis on single entry
        df = pd.DataFrame({
            'heart_rate_bpm': [hr], 'steps': [steps], 'sleep': [sleep]
        })
        df = process_full_analysis(df)
        status = df['severity'].iloc[0]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'INSERT INTO health_data (username, heart_rate, steps, sleep, status, entry_time) VALUES (%s, %s, %s, %s, %s, %s)',
            (username, hr, steps, sleep, status, entry_time)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash(f'Data saved! Status: {status}', 'success')
        return redirect(url_for('dashboard'))
    return render_template('data_entry.html')

@app.route('/dashboard')
@login_required
def dashboard():
    username = session['username']
    days = request.args.get('days', 7, type=int)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        '''SELECT * FROM health_data 
           WHERE username = %s 
           AND entry_time >= DATE_SUB(NOW(), INTERVAL %s DAY)
           ORDER BY entry_time ASC''',
        (username, days)
    )
    health_data = cursor.fetchall()
    cursor.close()
    conn.close()

    # Calculate stats
    avg_hr = round(sum(d['heart_rate'] for d in health_data) / len(health_data)) if health_data else 0
    avg_steps = round(sum(d['steps'] for d in health_data) / len(health_data)) if health_data else 0
    avg_sleep = round(sum(float(d['sleep']) for d in health_data) / len(health_data), 1) if health_data else 0

    # Prepare chart data
    chart_data = {
        'heart_rate': [d['heart_rate'] for d in health_data],
        'steps': [d['steps'] for d in health_data],
        'sleep': [float(d['sleep']) for d in health_data],
        'dates': [d['entry_time'].strftime('%Y-%m-%d %H:%M') for d in health_data],
        'status': [d['status'] for d in health_data] # Pass status for coloring
    }

    return render_template('dashboard.html',
                         health_data=health_data[-20:],
                         chart_data=chart_data,
                         avg_heart_rate=avg_hr,
                         avg_steps=avg_steps,
                         avg_sleep=avg_sleep,
                         days=days)

@app.route('/export_data')
@login_required
def export_data():
    # ... (keep existing export code) ...
    pass 

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get user info
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
    user = cursor.fetchone()

    # Get stats for the profile page
    cursor.execute('SELECT COUNT(*) as total_entries FROM health_data WHERE username = %s', (username,))
    stats = cursor.fetchone()

    if request.method == 'POST':
        # Handle Profile Update
        email = request.form['email']
        age = request.form['age']
        gender = request.form['gender']

        cursor.execute(
            'UPDATE users SET email = %s, age = %s, gender = %s WHERE username = %s',
            (email, age, gender, username)
        )
        conn.commit()
        flash('Profile updated successfully!', 'success')

        # Refresh user data
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('profile.html', user=user, stats=stats)

if __name__ == '__main__':
    app.run(debug=True)
