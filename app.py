from flask import Flask, request, redirect, render_template, session, flash, url_for
import string
import random
import json
import os
from urllib.parse import urlparse
import socket
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
from urllib.parse import unquote

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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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
                'urls': {},
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

# Update the snip_url route to handle editing
@app.route('/snip-url', methods=['GET', 'POST'])
@login_required
def snip_url():
    short_url = None
    error = None
    edit_id = request.args.get('edit', '').strip()
    edit_data = None

    users = load_users()
    user_urls = users[session['username']]['urls']
    
    if edit_id and edit_id in user_urls:
        edit_data = user_urls[edit_id]
        if isinstance(edit_data, dict):
            edit_data = edit_data['url']
    
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
                
                if custom_id:
                    if custom_id in urls and (not edit_id or custom_id != edit_id):
                        error = "Custom URL already exists"
                    elif not all(c in string.ascii_letters + string.digits + '-_' for c in custom_id):
                        error = "Custom URL can only contain letters, numbers, hyphens and underscores"
                    elif len(custom_id) > 20:
                        error = "Custom URL must be 20 characters or less"
                    else:
                        short_id = custom_id
                else:
                    if edit_id:
                        short_id = edit_id
                    else:
                        short_id = generate_short_id()
                        while short_id in urls:
                            short_id = generate_short_id()

                if not error:
                    url_data = {
                        'url': long_url,
                        'active': True,
                        'clicks': 0,
                        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # If editing, remove old entry first
                    if edit_id and edit_id in urls:
                        del urls[edit_id]
                        if edit_id in user_urls:
                            url_data['clicks'] = user_urls[edit_id].get('clicks', 0)
                            url_data['active'] = user_urls[edit_id].get('active', True)
                            url_data['created_at'] = user_urls[edit_id].get('created_at', 
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            del user_urls[edit_id]
                    
                    urls[short_id] = long_url
                    user_urls[short_id] = url_data
                    save_urls(urls)
                    users[session['username']]['urls'] = user_urls
                    save_users(users)
                    
                    if edit_id:
                        flash('URL updated successfully!', 'success')
                        return redirect(url_for('view_links'))
                    else:
                        short_url = request.host_url + short_id

    return render_template('index.html', 
                         short_url=short_url, 
                         error=error, 
                         username=session.get('username'),
                         edit_id=edit_id,
                         edit_url=unquote(edit_data) if edit_data else None)

@app.route('/<short_id>')
def redirect_short_url(short_id):
    urls = load_urls()
    users = load_users()
    
    if short_id in urls:
        for username, user_data in users.items():
            if short_id in user_data.get('urls', {}):
                url_data = user_data['urls'][short_id]
                if isinstance(url_data, dict) and not url_data.get('active', True):
                    if 'username' in session and session['username'] == username:
                        flash('This URL is currently inactive', 'error')
                        return redirect(url_for('view_links'))
                    return render_template('inactive.html'), 404
                
                if isinstance(url_data, dict):
                    user_data['urls'][short_id]['clicks'] = url_data.get('clicks', 0) + 1
                    save_users(users)
        
        return redirect(urls[short_id])
    return render_template('404.html'), 404

@app.route('/view-links')
@login_required
def view_links():
    users = load_users()
    user_data = users[session['username']]
    
    urls_data = []
    for short_id, url_info in user_data['urls'].items():
        if isinstance(url_info, dict):
            urls_data.append({
                'short_id': short_id,
                'long_url': url_info['url'],
                'active': url_info.get('active', True),
                'clicks': url_info.get('clicks', 0),
                'created_at': url_info.get('created_at', user_data.get('created_at', 'N/A'))
            })
        else:
            urls_data.append({
                'short_id': short_id,
                'long_url': url_info,
                'active': True,
                'clicks': 0,
                'created_at': user_data.get('created_at', 'N/A')
            })
    
    return render_template('view_links.html', 
                         username=session['username'],
                         urls=urls_data)

@app.route('/toggle-url/<short_id>')
@login_required
def toggle_url(short_id):
    users = load_users()
    username = session['username']
    
    if short_id in users[username]['urls']:
        if isinstance(users[username]['urls'][short_id], dict):
            users[username]['urls'][short_id]['active'] = not users[username]['urls'][short_id].get('active', True)
        else:
            users[username]['urls'][short_id] = {
                'url': users[username]['urls'][short_id],
                'active': False,
                'clicks': 0,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        save_users(users)
        flash('URL status updated', 'success')
    else:
        flash('URL not found', 'error')
    
    return redirect(url_for('view_links'))

@app.route('/analytics')
@login_required
def analytics():
    users = load_users()
    user_data = users[session['username']]
    
    total_links = len(user_data['urls'])
    total_clicks = 0
    most_popular = {'url': '', 'clicks': 0}
    active_links = 0
    clicks_by_day = {}
    
    for short_id, url_info in user_data['urls'].items():
        if isinstance(url_info, dict):
            clicks = url_info.get('clicks', 0)
            total_clicks += clicks
            
            if clicks > most_popular['clicks']:
                most_popular = {
                    'url': f"{request.host_url}{short_id}",
                    'clicks': clicks
                }
            
            if url_info.get('active', True):
                active_links += 1
            
            created_date = url_info.get('created_at', '').split()[0]
            clicks_by_day[created_date] = clicks_by_day.get(created_date, 0) + clicks
    
    # Sort clicks by day chronologically
    sorted_dates = sorted(clicks_by_day.keys())
    sorted_clicks = {date: clicks_by_day[date] for date in sorted_dates}
    
    return render_template('analytics.html',
                         username=session['username'],
                         total_links=total_links,
                         total_clicks=total_clicks,
                         active_links=active_links,
                         most_popular=most_popular,
                         clicks_by_day=sorted_clicks)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    users = load_users()
    user_data = users[session['username']]
    message = None

    if request.method == 'POST':
        new_username = request.form['username'].strip()
        new_email = request.form['email'].strip()
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if new_username != session['username']:
            if new_username in users:
                flash('Username already exists', 'error')
            else:
                users[new_username] = users.pop(session['username'])
                session['username'] = new_username
                message = 'Username updated successfully'

        if new_email != user_data['email']:
            users[session['username']]['email'] = new_email
            message = 'Email updated successfully'

        if new_password:
            if not check_password_hash(user_data['password'], current_password):
                flash('Current password is incorrect', 'error')
            elif new_password != confirm_password:
                flash('New passwords do not match', 'error')
            else:
                users[session['username']]['password'] = generate_password_hash(new_password)
                message = 'Password updated successfully'

        if message:
            save_users(users)
            flash(message, 'success')

        return redirect(url_for('settings'))

    return render_template('settings.html', 
                         username=session['username'],
                         email=user_data['email'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)