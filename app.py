import sqlite3
from flask import Flask, render_template, redirect, jsonify,url_for, request, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
from bs4 import BeautifulSoup
from openai import OpenAI



app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
DB_PATH = 'biasbridge.db'


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS surveys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                phase TEXT,
                stance TEXT,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uploaded_by TEXT,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS survey_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phase TEXT,
                question TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS survey_visibility (
                phase TEXT PRIMARY KEY,
                visible INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS debates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                country TEXT,
                date TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        # Seed example debates (skip if already exists)
        cursor.execute("SELECT COUNT(*) FROM debates")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO debates (topic, country, date) VALUES (?, ?, ?)",
                [
                    ("Gun Control Legislation", "South Korea", "2025.03.25"),
                    ("Forgiving student loan debt", "South Korea", "2025.03.18"),
                    ("Presidential Impeachment", "South Korea", "2025.03.10")
                ]
            )
        conn.commit()

def is_admin():
    return session.get('username') == 'test@test.com'
@app.route('/create-debate', methods=['GET', 'POST'])
def create_debate():
    if not is_admin():
        flash("Admin access required.")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        topic = request.form['topic']
        country = request.form['country']
        date = request.form['date']

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO debates (topic, country, date, is_active) VALUES (?, ?, ?, ?)",
                           (topic, country, date, 1))
            conn.commit()
        flash("Debate created.")
        return redirect(url_for('dashboard'))

    return render_template('create_debate.html')
@app.route('/close-debate/<int:debate_id>', methods=['POST'])
def close_debate(debate_id):
    if not is_admin():
        flash("Admin access required.")
        return redirect(url_for('dashboard'))

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE debates SET is_active = 0 WHERE id = ?", (debate_id,))
        conn.commit()
    flash("Debate closed.")
    return redirect(url_for('dashboard'))

# Utility Functions
def get_user_by_username(username):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
        return cursor.fetchone()

def add_user(username, hashed_password):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()

# Routes
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/save-note/<week>', methods=['POST'])
def save_note(week):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    html_content = data.get('html', '')

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                week TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute("INSERT INTO notes (user_id, week, content) VALUES (?, ?, ?)",
                       (session['user_id'], week, html_content))
        conn.commit()

    return jsonify({"status": "Note saved"})


@app.route('/summarize-note/<week>', methods=['POST'])
def summarize_note(week):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    html_content = data.get('html', '')

    soup = BeautifulSoup(html_content, 'html.parser')
    plain_text = soup.get_text(separator=' ', strip=True)

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes notes from a debate."},
                {"role": "user", "content": f"Summarize the following debate notes in 2-3 concise sentences:\n\n{plain_text}"}
            ],
            temperature=0.7
        )
        summary = response.choices[0].message.content.strip()

        summarized_html = html_content + f"<p><strong>Summary:</strong> {summary}</p>"

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO notes (user_id, week, content) VALUES (?, ?, ?)",
                           (session['user_id'], week, summarized_html))
            conn.commit()

        return jsonify({"summary": summary})
    except Exception as e:
        print("Error during summarization:", e)
        return jsonify({"error": "Summarization failed"}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if get_user_by_username(username):
            flash("Username already exists.")
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        add_user(username, hashed_password)
        flash("Registration successful. Please log in.")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('dashboard'))
        flash("Invalid credentials.")
    return render_template('login.html')

@app.route('/mypage')
def mypage():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    username = session['username']

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Get all debates the user participated in
        cursor.execute('''
            SELECT d.id, d.topic, s.stance
            FROM surveys s
            JOIN debates d ON d.id = s.debate_id
            WHERE s.user_id = ?
        ''', (user_id,))
        user_stances = cursor.fetchall()

        # For each debate, get aggregate counts
        debate_summaries = {}
        for debate_id, topic, user_stance in user_stances:
            cursor.execute('''
                SELECT stance, COUNT(*) 
                FROM surveys 
                WHERE debate_id = ?
                GROUP BY stance
            ''', (debate_id,))
            counts = dict(cursor.fetchall())
            summary = {
                'support': counts.get('support', 0),
                'oppose': counts.get('oppose', 0),
                'neutral': counts.get('neutral', 0),
                'user_stance': user_stance
            }
            debate_summaries[topic] = summary

    return render_template("mypage.html", username=username, debate_summaries=debate_summaries)


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Get all active debates
        cursor.execute("SELECT id, topic, country, date, is_active FROM debates WHERE is_active = 1 ORDER BY date DESC")
        current_debates = cursor.fetchall()

        # Get all closed debates
        cursor.execute("SELECT id, topic, country, date, is_active FROM debates WHERE is_active = 0 ORDER BY date DESC")
        past_debates = cursor.fetchall()

    return render_template('dashboard.html',
                           username=session['username'],
                           is_admin=is_admin(),
                           current_debates=current_debates,
                           past_debates=past_debates)



@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('index'))

@app.route('/debate')
def debate():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    current_user = session['username']
    user_id = session['user_id']
    assigned_side = session.get('side')
    if not assigned_side:
        assigned_side = random.choice(['left', 'right'])
        session['side'] = assigned_side

    user_display = f"{current_user} ({current_user}@email.com)"
    left_group = ['ADMIN KIM (admin@admin.com)']
    right_group = ['ADMIN KIM (admin@admin.com)']

    if assigned_side == 'left':
        left_group.append(user_display)
    else:
        right_group.append(user_display)

    def count_stances(phase):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT stance FROM surveys WHERE phase = ?", (phase,))
            data = cursor.fetchall()
            counts = {'support': 0, 'oppose': 0, 'neutral': 0}
            for (stance,) in data:
                if stance in counts:
                    counts[stance] += 1
        return counts

    def has_submitted(phase):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM surveys WHERE user_id = ? AND phase = ?", (user_id, phase))
            return cursor.fetchone() is not None

    pre = count_stances('pre')
    post = count_stances('post')
    pre_submitted = has_submitted('pre')
    post_submitted = has_submitted('post')

    return render_template('debate.html',
                           username=current_user,
                           topic="PRESIDENT IMPEACHMENT",
                           country="South Korea",
                           date="2025. 04. 01",
                           left_group=left_group,
                           right_group=right_group,
                           pre_data=list(pre.values()),
                           post_data=list(post.values()),
                           pre_submitted=pre_submitted,
                           post_submitted=post_submitted)

@app.route('/survey/<phase>', methods=['POST'])
def submit_survey(phase):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session['user_id']

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM surveys WHERE user_id = ? AND phase = ?", (user_id, phase))
        already_submitted = cursor.fetchone()

        if already_submitted:
            if request.is_json:
                return jsonify({"status": "duplicate"})
            flash("You have already submitted this survey.")
            return redirect(url_for('debate'))

        # Get data from form or JSON
        if request.is_json:
            data = request.get_json()
            stance = data.get('stance')
            comment = data.get('comment', '')
        else:
            stance = request.form.get('stance')
            comment = request.form.get('comment', '')

        # Insert the survey
        cursor.execute(
            "INSERT INTO surveys (user_id, phase, stance, comment) VALUES (?, ?, ?, ?)",
            (user_id, phase, stance, comment)
        )
        conn.commit()

        def count_stances(ph):
            cursor.execute("SELECT stance FROM surveys WHERE phase = ?", (ph,))
            data = cursor.fetchall()
            counts = {'support': 0, 'oppose': 0, 'neutral': 0}
            for (s,) in data:
                if s in counts:
                    counts[s] += 1
            return [counts['support'], counts['oppose'], counts['neutral']]

        if request.is_json:
            return jsonify({
                "status": "ok",
                "pre": count_stances("pre"),
                "post": count_stances("post")
            })
        else:
            return redirect(url_for('debate'))

    flash("Survey submitted!")
    return redirect(url_for('debate'))

@app.route('/get-survey-data')
def get_survey_data():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    def count_stances(phase):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT stance FROM surveys WHERE phase = ?", (phase,))
            data = cursor.fetchall()
            counts = {'support': 0, 'oppose': 0, 'neutral': 0}
            for (stance,) in data:
                if stance in counts:
                    counts[stance] += 1
            return counts

    pre = count_stances('pre')
    post = count_stances('post')
    return jsonify({
        "pre": [pre['support'], pre['oppose'], pre['neutral']],
        "post": [post['support'], post['oppose'], post['neutral']]
    })

@app.route('/comment', methods=['POST'])
def submit_comment():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    comment = request.form['comment']
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO comments (user_id, comment) VALUES (?, ?)", (session['user_id'], comment))
        conn.commit()
    flash("Comment submitted.")
    return redirect(url_for('debate'))

@app.route('/moderator-summary', methods=['POST'])
def submit_summary():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    summary = request.form['summary']
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO summaries (uploaded_by, summary) VALUES (?, ?)", (session['username'], summary))
        conn.commit()
    flash("Summary uploaded.")
    return redirect(url_for('debate'))
@app.route('/debate/<int:debate_id>')
def view_debate(debate_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT topic, country, date FROM debates WHERE id = ?", (debate_id,))
        debate = cursor.fetchone()

    if not debate:
        flash("Debate not found.")
        return redirect(url_for('dashboard'))

    topic, country, date = debate

    return render_template('debate_view.html', topic=topic, country=country, date=date)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
