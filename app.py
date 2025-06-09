from flask import Flask, request, redirect, render_template
import string
import random
import json
import os
from urllib.parse import urlparse
import socket

app = Flask(__name__)

DATA_FILE = 'urls.json'

# Load or create URL mapping storage
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)

def load_urls():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_urls(urls):
    with open(DATA_FILE, 'w') as f:
        json.dump(urls, f, indent=4)

def generate_short_id(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def domain_exists(domain):
    try:
        socket.gethostbyname(domain)
        return True
    except socket.gaierror:
        return False

# Landing page (home)
@app.route('/', methods=['GET'])
def home():
    return render_template('landing.html')

# Main shortener form and result
@app.route('/snip-url', methods=['GET', 'POST'])
def snip_url():
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
                
                # If custom ID is provided
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
                    # Generate random ID if no custom ID provided
                    short_id = generate_short_id()
                    while short_id in urls:
                        short_id = generate_short_id()

                if not error:
                    urls[short_id] = long_url
                    save_urls(urls)
                    short_url = request.host_url + short_id

    return render_template('index.html', short_url=short_url, error=error)

@app.route('/<short_id>')
def redirect_short_url(short_id):
    urls = load_urls()
    long_url = urls.get(short_id)
    if long_url:
        return redirect(long_url)
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)