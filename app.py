from flask import Flask, request, redirect, render_template, session, flash, url_for
import string
import random
import json
import os
from urllib.parse import urlparse
import socket
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a random secret key

# Data files
DATA_FILE = 'urls.json'
USERS_FILE = 'users.json'

# Initialize data files if they don't exist
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({}, f)

def load_urls():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_urls(urls):
    with open(DATA_FILE, 'w') as f:
        json.dump(urls, f, indent=4)

def load_users():
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def generate_short_id(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def domain_exists(domain):
    try:
        socket.gethostbyname(domain)
        return True
    except socket.gaierror:
        return False

@app.route('/')
def home():
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        users = load_users()

        if not username or not email or not password:
            flash('All fields are required', 'error')
        elif password != confirm_password:
            flash('Passwords do not match', 'error')
        elif username in users:
            flash('Username already exists', 'error')
        else:
            users[username] = {
                'email': email,
                'password': generate_password_hash(password),
                'urls': {}
            }
            save_users(users)
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        users = load_users()

        if username in users and check_password_hash(users[username]['password'], password):
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('snip_url'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))

@app.route('/snip-url', methods=['GET', 'POST'])
def snip_url():
    if 'username' not in session:
        flash('Please login to shorten URLs', 'error')
        return redirect(url_for('login'))

    short_url = None
    error = None

    if request.method == 'POST':
        long_url = request.form['long_url'].strip()
        custom_id = request.form.get('custom_id', '').strip()

        # Parse and validate URL
        parsed_url = urlparse(long_url)
        if not parsed_url.scheme:
            long_url = 'http://' + long_url
            parsed_url = urlparse(long_url)

        if parsed_url.scheme not in ('http', 'https') or not parsed_url.netloc:
            error = "URL is Invalid"
        else:
            domain = parsed_url.netloc
            if not domain_exists(domain):
                error = "URL domain does not exist"
            else:
                urls = load_urls()
                user_urls = load_users()[session['username']]['urls']
                
                if custom_id:
                    if custom_id in urls:
                        error = "Custom URL already exists"
                    elif not all(c in string.ascii_letters + string.digits + '-_' for c in custom_id):
                        error = "Custom URL can only contain letters, numbers, hyphens and underscores"
                    elif len(custom_id) > 20:
                        error = "Custom URL must be 20 characters or less"
                    else:
                        short_id = custom_id
                else:
                    short_id = generate_short_id()
                    while short_id in urls:
                        short_id = generate_short_id()

                if not error:
                    urls[short_id] = long_url
                    user_urls[short_id] = long_url
                    save_urls(urls)
                    users = load_users()
                    users[session['username']]['urls'] = user_urls
                    save_users(users)
                    short_url = request.host_url + short_id

    return render_template('index.html', short_url=short_url, error=error, username=session.get('username'))

@app.route('/<short_id>')
def redirect_short_url(short_id):
    urls = load_urls()
    long_url = urls.get(short_id)
    if long_url:
        return redirect(long_url)
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)