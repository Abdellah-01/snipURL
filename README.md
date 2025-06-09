# 🔗 Snip URL

**Snip URL** is a lightweight, Flask-based URL shortener that allows users to convert long URLs into short, shareable links. It verifies domain validity and stores mappings locally using a JSON file—ideal for learning projects, prototyping, or small-scale use.

---

## 🚀 Features

- ✅ Shortens long URLs to compact 6-character codes
- 🌐 Validates domain before shortening
- 🔒 Automatically adds missing `http://` or `https://` scheme
- 🔁 Redirects short URLs to the original destination
- 💾 Stores URL mappings in a local JSON file
- 🖥️ Simple, responsive web interface using HTML templates

---

## 📸 Demo

> _Add a screenshot or screen recording here for better context_

---

## 📁 Project Structure

Snip-URL/
├── templates/
│ ├── index.html # Page to enter long URL and get short one
│ └── landing.html # Landing or home page
├── urls.json # Stores short-to-long URL mappings
├── app.py # Main Flask application
└── README.md # Project documentation


---

## 💡 How It Works

1. User accesses `/snip-url` to input a long URL.
2. The server verifies the domain's existence using DNS lookup.
3. If valid, a random 6-character alphanumeric code is generated.
4. The long URL is mapped to this code and stored in `urls.json`.
5. A short URL (e.g., `http://localhost:5000/abc123`) is returned.
6. Visiting the short URL redirects the user to the original destination.

---

## 🛠 Tech Stack

- **Backend:** Python 3, Flask
- **Frontend:** HTML, Jinja2 templates
- **Storage:** Local JSON file (no database)

---

## 🔧 Setup Instructions

### ✅ Prerequisites

- Python 3.x installed

### 📦 Installation Steps

1. **Clone the repository:**

```bash
git clone https://github.com/your-username/snip-url.git
cd snip-url

2. **Create and activate a virtual environment:**
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. **Install Dependecies**
pip install flask

4. **Run the Application**
python app.py

5. **Open your browser and navigate to:**
http://localhost:5000/


### ✨ Usage
- Visit http://localhost:5000/ to access the landing page.
- Go to /snip-url to input a long URL.
- Submit the form to receive a shortened URL.
- Use the short URL in your browser—it redirects to the original.


### 🤝 Contributing
- Pull requests are welcome! If you'd like to:
- Report bugs
- Request features
- Improve the UI
- Optimize code

...then open an issue or submit a PR.
