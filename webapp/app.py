import os
import uuid
import bcrypt
import psycopg2
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash

# --- App and Session Configuration ---
app = Flask(__name__)
# A strong secret key is vital for session security
app.config['SECRET_KEY'] = os.urandom(24) 
# Set session to be permanent so timeout is respected
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=1) # Q4(e) 1-minute timeout

# --- Database Configuration ---
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
        return conn
    except psycopg2.OperationalError as e:
        # This helps in debugging connection issues
        print(f"Could not connect to database: {e}")
        return None

def init_db():
    """Initializes the database table and creates the default user if they don't exist."""
    conn = get_db_connection()
    if conn is None:
        print("Skipping DB initialization due to connection failure.")
        return
        
    cur = conn.cursor()
    # Create table if it doesn't exist
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    ''')
    
    # Q4(b): Check if the 'student' user exists
    cur.execute("SELECT * FROM users WHERE username = 'student';")
    user_exists = cur.fetchone()
    
    if not user_exists:
        # Q4(b) & Q4(c): Create user with a cryptographically hashed password
        student_id = '2301769'
        # Generate a salt and hash the password using bcrypt
        hashed_password = bcrypt.hashpw(student_id.encode('utf-8'), bcrypt.gensalt())
        
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            ('student', hashed_password.decode('utf-8'))
        )
        print("Default user 'student' created.")
        
    conn.commit()
    cur.close()
    conn.close()

# --- Routes ---

@app.route('/')
def home():
    """Renders the login page."""
    # If user is already logged in, redirect to dashboard
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """Handles the login form submission."""
    username = request.form['username']
    password = request.form['password']
    
    conn = get_db_connection()
    # --- ADD THIS BLOCK TO HANDLE CONNECTION FAILURE ---
    if conn is None:
        flash('A server error occurred. Please try again later.')
        return redirect(url_for('home'))
    # ---------------------------------------------------
        
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username = %s;", (username,))
    user_record = cur.fetchone()
    cur.close()
    conn.close()
    
    # Q4(c): Verify password against the stored hash using a secure comparison function
    if user_record and bcrypt.checkpw(password.encode('utf-8'), user_record[0].encode('utf-8')):
        # Password matches, set up the session
        session.permanent = True
        session['logged_in'] = True
        session['username'] = username
        # Q4(g): Generate a long, unique, and random session ID for display
        session['display_session_id'] = str(uuid.uuid4())
        
        return redirect(url_for('dashboard'))
    else:
        # Invalid credentials
        flash('Invalid username or password. Please try again.')
        return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    """Displays the dashboard for a logged-in user."""
    # Protect this page, redirect to login if not logged in
    if 'logged_in' in session:
        # Q4(d): Display page with session id and logout button
        return render_template('dashboard.html', session_id=session.get('display_session_id'))
    
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    """Logs the user out."""
    # Q4(f): Clear the session and return to the login page
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('home'))


# --- Main Execution ---
if __name__ == '__main__':
    # Initialize the database on startup
    init_db()
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)