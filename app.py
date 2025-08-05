import sqlite3
from flask import Flask, render_template, redirect, jsonify,url_for, request, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
from bs4 import BeautifulSoup
from openai import OpenAI
import requests
import pandas as pd
from polimbti import calculate_political_type_from_categories

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
DB_PATH = 'biasbridge.db'
UPLOAD_FOLDER = 'static/debate_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



from collections import defaultdict

def get_category_averages(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT topic, score
            FROM topic_alignment_scores
            WHERE user_id = ?
        ''', (user_id,))
        rows = cursor.fetchall()

    # Assuming `topic` is the category name (e.g., "Globalism")
    category_scores = defaultdict(list)
    for category, score in rows:
        category_scores[category].append(float(score))

    # Average score per category
    return {
        cat: sum(scores) / len(scores)
        for cat, scores in category_scores.items()
    }


def generate_central_view(topic):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a neutral political analyst."},
                {"role": "user", "content": f"Write a balanced and objective paragraph explaining the central view on the topic: '{topic}'."}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print("Central view generation failed:", e)
        return "Central view is not available at the moment."

import re
def expand_topic_for_search(topic, debate_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT search_keywords FROM debates WHERE id = ?", (debate_id,))
        row = cursor.fetchone()

        if row and row[0]:
            return row[0]  # return cached keywords

    # If not cached, generate using GPT
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You generate related keywords for a news search query."
                },
                {
                    "role": "user",
                    "content": f"List keywords related to this topic for news search. Only comma-separated keywords, no numbering: {topic}"
                }
            ],
            temperature=0.5
        )
        content = response.choices[0].message.content
        phrases = re.split(r'[,\n]', content)
        words = set()
        for phrase in phrases:
            for word in phrase.strip().split():
                clean = re.sub(r'\W+', '', word).lower()
                if clean:
                    words.add(clean)

        search_query = " OR ".join(words)

        # Cache the result
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE debates SET search_keywords = ? WHERE id = ?", (search_query, debate_id))
            conn.commit()

        return search_query
    except Exception as e:
        print("Failed to expand topic:", e)
        return topic
def fetch_news(topic, debate_id):
    search_query = expand_topic_for_search(topic, debate_id)
    url = f"https://newsapi.org/v2/everything?q={search_query}&language=en&sortBy=relevancy&pageSize=15&apiKey={NEWS_API_KEY}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            return [
                {
                    'title': article['title'],
                    'url': article['url'],
                    'description': article['description'],
                    'publishedAt': article['publishedAt'],
                    'source': article['source']['name']
                }
                for article in articles
            ]
        else:
            print(f"NewsAPI Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print("Error fetching news:", e)
        return []



def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_group (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                debate_id INTEGER,
                group_name TEXT CHECK(group_name IN ('support', 'oppose')),
                UNIQUE(user_id, debate_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS week_completion (
                user_id INTEGER,
                debate_id INTEGER,
                week TEXT,
                PRIMARY KEY (user_id, debate_id, week)
            )
        ''')

        conn.commit()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                firstname TEXT,
                lastname TEXT
            )
        ''')

        # Debates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS debates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                country TEXT,
                date TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')

        # Add 'image' column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE debates ADD COLUMN image TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Week completion table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS week_completion (
                user_id INTEGER,
                debate_id INTEGER,
                week TEXT,
                PRIMARY KEY (user_id, debate_id, week)
            )
        ''')
        # Debate side assignment
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_debate_roles (
                user_id INTEGER,
                debate_id INTEGER,
                side TEXT CHECK(side IN ('support', 'oppose')),
                PRIMARY KEY (user_id, debate_id)
            )
        ''')

        # Surveys table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS surveys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                phase TEXT,
                stance TEXT,
                comment TEXT,
                debate_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Alignment results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alignment_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                debate_id INTEGER,
                phase TEXT,
                alignment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, debate_id, phase)
            )
        ''')

        # Comments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Summaries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uploaded_by TEXT,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Survey questions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS survey_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phase TEXT,
                question TEXT
            )
        ''')

        # Survey visibility table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS survey_visibility (
                phase TEXT PRIMARY KEY,
                visible INTEGER DEFAULT 0
            )
        ''')

        # Notes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                week TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert default debates if none exist
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
        cursor.execute("PRAGMA table_info(debates)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'central_view' not in columns:
            cursor.execute("ALTER TABLE debates ADD COLUMN central_view TEXT")
        conn.commit()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(debates)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'search_keywords' not in columns:
                cursor.execute("ALTER TABLE debates ADD COLUMN search_keywords TEXT")
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
        raw_date = request.form['date']  # e.g. '2025-06-10'
        date = raw_date.replace('-', '.')  # Convert to '2025.06.10'

        image = request.files.get('image')
        image_filename = None

        if image and image.filename:
            image_filename = f"{topic.replace(' ', '_')}_{random.randint(1000, 9999)}.png"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("ALTER TABLE debates ADD COLUMN image TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists, ignore

            cursor.execute(
                "INSERT INTO debates (topic, country, date, is_active, image) VALUES (?, ?, ?, ?, ?)",
                (topic, country, date, 1, image_filename)
            )
            conn.commit()
        flash("Debate created.")
        return redirect(url_for('dashboard'))

    return render_template('create_debate.html')


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

def add_user(username, hashed_password, firstname, lastname):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, firstname, lastname) VALUES (?, ?, ?, ?)",
            (username, hashed_password, firstname, lastname)
        )
        conn.commit()

@app.route('/save-alignment/<int:debate_id>', methods=['POST'])
def save_alignment(debate_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data = request.get_json()
    phase = data.get('phase')
    topic_scores = data.get('topic_scores', {})

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for topic, score in topic_scores.items():
        c.execute('''
            INSERT INTO topic_alignment_scores (user_id, debate_id, topic, phase, score)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, debate_id, topic, phase)
            DO UPDATE SET score = excluded.score
        ''', (user_id, debate_id, topic, phase, score))
    conn.commit()
    conn.close()

    return jsonify({'success': True})



# Routes
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/save-note/<int:debate_id>/<week>', methods=['POST'])
def save_note(debate_id, week):
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
                debate_id INTEGER,
                week TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, debate_id, week)
            )
        ''')

        cursor.execute('''
            INSERT INTO notes (user_id, debate_id, week, content)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, debate_id, week)
            DO UPDATE SET content = excluded.content, created_at = CURRENT_TIMESTAMP
        ''', (session['user_id'], debate_id, week, html_content))

        conn.commit()

    return jsonify({"status": "Note saved"})

@app.route('/summarize-note/<int:debate_id>/<week>', methods=['POST'])
def summarize_note(debate_id, week):
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

        summarized_html = html_content + f"<strong>Summary:</strong> {summary}</p>"

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO notes (user_id, debate_id, week, content)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, debate_id, week)
                DO UPDATE SET content = excluded.content, created_at = CURRENT_TIMESTAMP
            ''', (session['user_id'], debate_id, week, summarized_html))

            conn.commit()

        return jsonify({"summary": summary})
    except Exception as e:
        print("Error during summarization:", e)
        return jsonify({"error": "Summarization failed"}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        username = request.form['username']  # Email
        password = request.form['password']

        if get_user_by_username(username):
            flash("Email already exists.")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        add_user(username, hashed_password, firstname, lastname)

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
        flash("Invalid username or password.")
    return render_template('login.html')
@app.route('/mypage')
def mypage():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    username = session.get('username')

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Get debate details
        cursor.execute('SELECT id, topic, date FROM debates')
        debates = cursor.fetchall()

        debate_details = {}

        for debate_id, topic, date in debates:
            # Get stances and alignments
            cursor.execute('''
                SELECT stance, comment FROM surveys WHERE user_id = ? AND debate_id = ? AND phase = 'pre'
            ''', (user_id, debate_id))
            pre = cursor.fetchone()

            cursor.execute('''
                SELECT stance, comment FROM surveys WHERE user_id = ? AND debate_id = ? AND phase = 'post'
            ''', (user_id, debate_id))
            post = cursor.fetchone()

            cursor.execute('''
                SELECT alignment FROM alignment_results WHERE user_id = ? AND debate_id = ? AND phase = 'pre'
            ''', (user_id, debate_id))
            alignment_pre = cursor.fetchone()
            cursor.execute('''
                SELECT alignment FROM alignment_results WHERE user_id = ? AND debate_id = ? AND phase = 'post'
            ''', (user_id, debate_id))
            alignment_post = cursor.fetchone()

            # Get topic scores
            cursor.execute('''
                SELECT topic, phase, score FROM topic_alignment_scores
                WHERE user_id = ? AND debate_id = ?
            ''', (user_id, debate_id))
            topic_scores = cursor.fetchall()

            score_dict = {}
            for t, phase, score in topic_scores:
                score_dict.setdefault(t, {})[phase] = score

            debate_details[topic] = {
                'debate_id': debate_id,
                'date': date,
            }

        # Average alignment score
        cursor.execute('''
            SELECT alignment FROM alignment_results
            WHERE user_id = ? AND alignment IS NOT NULL
        ''', (user_id,))
        alignments = [row[0] for row in cursor.fetchall()]

    alignment_map = {'left': -1, 'center': 0, 'right': 1}
    scores = [alignment_map[a] for a in alignments if a in alignment_map]

    if scores:
        avg_score = sum(scores) / len(scores)
        if avg_score < -0.5:
            avg_label = "Left"
        elif avg_score > 0.5:
            avg_label = "Right"
        else:
            avg_label = "Center"
    else:
        avg_score = 'N/A'
        avg_label = 'N/A'
    category_avg = get_category_averages(user_id)
    politicmbti_result = calculate_political_type_from_categories(category_avg)

    # Pass pre and post data aggregated across all debates
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT topic, AVG(score)
            FROM topic_alignment_scores
            WHERE user_id = ? AND phase = 'pre'
            GROUP BY topic
        ''', (user_id,))
        pre_data = {row[0]: round(row[1], 2) for row in cursor.fetchall()}

        cursor.execute('''
            SELECT topic, AVG(score)
            FROM topic_alignment_scores
            WHERE user_id = ? AND phase = 'post'
            GROUP BY topic
        ''', (user_id,))
        post_data = {row[0]: round(row[1], 2) for row in cursor.fetchall()}

    # Generate mock group average using existing utility
    topics = list(set(pre_data.keys()) | set(post_data.keys()))
    group_average = get_mock_group_average(topics)

    return render_template(
        'mypage.html',
        username=username,
        debate_details=debate_details,
        avg_alignment_score=avg_score,
        avg_alignment_label=avg_label,
        politicmbti=politicmbti_result,
        pre_data=pre_data,
        post_data=post_data,
        group_average=group_average
    )


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Get all active debates
        cursor.execute(
            "SELECT id, topic, country, date, is_active, image FROM debates WHERE is_active = 1 ORDER BY date DESC")
        current_debates = cursor.fetchall()

        # Get all closed debates
        cursor.execute(
            "SELECT id, topic, country, date, is_active, image FROM debates WHERE is_active = 0 ORDER BY date DESC")
        past_debates = cursor.fetchall()

    return render_template('dashboard.html',
                           username=session['username'],
                           is_admin=is_admin(),
                           current_debates=current_debates,
                           past_debates=past_debates)

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def check_alignment_completion(user_id, debate_id, phase):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT topic, score
        FROM topic_alignment_scores
        WHERE user_id = ? AND debate_id = ? AND phase = ?
    """, (user_id, debate_id, phase))

    rows = cursor.fetchall()
    conn.close()

    if rows:
        topic_scores = {topic: float(score) for topic, score in rows}
        print("ABC")
        return True, topic_scores
    else:
        print("DEF")
        return False, {}



@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('index'))
@app.route("/debate/<int:debate_id>")
def debate(debate_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    alignment_questions = load_alignment_questions()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Get debate info (now includes image)
        cursor.execute("SELECT topic, country, date, is_active, image FROM debates WHERE id = ?", (debate_id,))
        row = cursor.fetchone()
        if not row:
            flash("Debate not found.", "danger")
            return redirect(url_for("dashboard"))
        topic, country, date, is_active, image = row

        # Assign group if not already assigned
        cursor.execute("SELECT group_name FROM user_group WHERE user_id = ? AND debate_id = ?", (user_id, debate_id))
        result = cursor.fetchone()
        first_assignment = False
        if not result:
            group_name = random.choice(["support", "oppose"])
            cursor.execute("INSERT INTO user_group (user_id, debate_id, group_name) VALUES (?, ?, ?)",
                           (user_id, debate_id, group_name))
            conn.commit()
            first_assignment = True
        else:
            group_name = result[0]

        # Get group members (support)
        cursor.execute('''
            SELECT u.username, u.firstname
            FROM user_group g
            JOIN users u ON u.id = g.user_id
            WHERE g.debate_id = ? AND g.group_name = 'support'
        ''', (debate_id,))
        left_group = [{'name': row[1], 'email': row[0]} for row in cursor.fetchall()]
        if not row[4]:  # image is at index 4, so fetch central_view explicitly
            cursor.execute("SELECT central_view FROM debates WHERE id = ?", (debate_id,))
            central_view_paragraph = cursor.fetchone()[0]

        is_generating_view = False
        if not central_view_paragraph:
            is_generating_view = True
            central_view_paragraph = generate_central_view(topic)
            cursor.execute("UPDATE debates SET central_view = ? WHERE id = ?", (central_view_paragraph, debate_id))
            conn.commit()

        # Get group members (oppose)
        cursor.execute('''
            SELECT u.username, u.firstname
            FROM user_group g
            JOIN users u ON u.id = g.user_id
            WHERE g.debate_id = ? AND g.group_name = 'oppose'
        ''', (debate_id,))
        right_group = [{'name': row[1], 'email': row[0]} for row in cursor.fetchall()]

        # Determine admin
        is_admin_flag = is_admin()

        # Alignment info
        cursor.execute("SELECT alignment FROM alignment_results WHERE user_id = ? AND debate_id = ?", (user_id, debate_id))
        alignment_data = [r[0] for r in cursor.fetchall()]
        alignment_pre = alignment_data[0] if len(alignment_data) > 0 else None
        alignment_post = alignment_data[1] if len(alignment_data) > 1 else None

        # Survey info
        cursor.execute("SELECT 1 FROM surveys WHERE user_id = ? AND debate_id = ? AND phase = 'pre'", (user_id, debate_id))
        pre_submitted = cursor.fetchone() is not None
        cursor.execute("SELECT 1 FROM surveys WHERE user_id = ? AND debate_id = ? AND phase = 'post'", (user_id, debate_id))
        post_submitted = cursor.fetchone() is not None

        # Completed weeks info
        cursor.execute("SELECT week FROM week_completion WHERE user_id = ? AND debate_id = ?", (user_id, debate_id))
        weeks_done = [row[0] for row in cursor.fetchall()]
        week1_done = "week1" in weeks_done
        week2_done = "week2" in weeks_done
    if image is None:
        image = 'images/login_bg.jpg'
    else:
        image = 'debate_images/'+image
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT week, content FROM notes
            WHERE user_id = ? AND debate_id = ?
        ''', (user_id, debate_id))
        notes = cursor.fetchall()
        saved_notes = {row[0]: row[1] for row in notes} if notes else {}
    news_articles = fetch_news(topic, debate_id)
    alignment_questions = load_alignment_questions()
    topics = [q['Topic'] for q in alignment_questions]
    group_average = get_mock_group_average(topics)
    pre_done, pre_data = check_alignment_completion(user_id, debate_id, "pre")
    post_done, post_data = check_alignment_completion(user_id, debate_id, "post")
    return render_template(
        "debate.html",
        debate_id=debate_id,
        topic=topic,
        pre_done=pre_done,
        post_done=post_done,
        pre_data= pre_data,
        post_data= post_data,
        country=country,
        date=date,
        alignment_questions=alignment_questions,
        group_average=group_average,
        saved_notes=saved_notes,
        central_view=central_view_paragraph,
        is_admin=is_admin_flag,
        left_group=left_group,
        news_articles=news_articles,
        is_generating_view=is_generating_view,
        right_group=right_group,
        alignment_pre=alignment_pre,
        alignment_post=alignment_post,
        group_name=group_name,
        first_assignment=first_assignment,
        pre_submitted=pre_submitted,
        post_submitted=post_submitted,
        week1_done=week1_done,
        week2_done=week2_done,
        debate_image= image
    )


@app.route('/mark-week-complete/<int:debate_id>/<week>', methods=['POST'])
def mark_week_complete(debate_id, week):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    current_user = session['user_id']

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        if is_admin():
            # Get all registered users
            cursor.execute('SELECT id FROM users')
            user_ids = [row[0] for row in cursor.fetchall()]

            # Mark the week as complete for each user
            for user_id in user_ids:
                cursor.execute('''
                    INSERT OR IGNORE INTO week_completion (user_id, debate_id, week)
                    VALUES (?, ?, ?)
                ''', (user_id, debate_id, week))
        else:
            # Normal user completes week only for themselves
            cursor.execute('''
                INSERT OR IGNORE INTO week_completion (user_id, debate_id, week)
                VALUES (?, ?, ?)
            ''', (current_user, debate_id, week))

        conn.commit()

    return jsonify({'status': 'ok'})



@app.route('/survey/<phase>', methods=['POST'])
def submit_survey(phase):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session['user_id']
    debate_id = request.args.get("debate_id")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Ensure survey is per-user per-debate per-phase
        cursor.execute("SELECT 1 FROM surveys WHERE user_id = ? AND phase = ? AND debate_id = ?",
                       (user_id, phase, debate_id))
        already_submitted = cursor.fetchone()
        if already_submitted:
            if request.is_json:
                return jsonify({"status": "duplicate"})
            flash("You have already submitted this survey.")
            return redirect(url_for('debate', debate_id=debate_id))

        if request.is_json:
            data = request.get_json()
            stance = data.get('stance')
            comment = data.get('comment', '')
        else:
            stance = request.form.get('stance')
            comment = request.form.get('comment', '')

        cursor.execute(
            "INSERT INTO surveys (user_id, phase, stance, comment, debate_id) VALUES (?, ?, ?, ?, ?)",
            (user_id, phase, stance, comment, debate_id)
        )
        conn.commit()

        def count_stances(ph):
            cursor.execute("SELECT stance FROM surveys WHERE phase = ? AND debate_id = ?", (ph, debate_id))
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
            return redirect(url_for('debate', debate_id=debate_id))

@app.route('/get-survey-data')
def get_survey_data():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    debate_id = request.args.get("debate_id")
    if not debate_id:
        return jsonify({"error": "Missing debate_id"}), 400

    def count_stances(phase):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT stance FROM surveys WHERE phase = ? AND debate_id = ?", (phase, debate_id))
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

def get_mock_group_average(topics):
    return {topic: round(random.uniform(2.0, 4.0), 2) for topic in topics}

def load_alignment_questions():
    df = pd.read_csv("static/sa_questions.csv")
    # df = df[:7]
    # return df.to_dict(orient='records')
    df_unique = df.drop_duplicates(subset="Topic", keep="first")  # One question per topic
    return df_unique.to_dict(orient='records')
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
# Add this block in view_debate route in app.py
@app.route('/view-debate/<int:debate_id>')
def view_debate(debate_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT topic, country, date FROM debates WHERE id = ?", (debate_id,))
        debate = cursor.fetchone()
        if not debate:
            flash("Debate not found.")
            return redirect(url_for('dashboard'))

        topic, country, date = debate

        def get_counts(phase):
            cursor.execute("SELECT stance FROM surveys WHERE debate_id = ? AND phase = ?", (debate_id, phase))
            data = cursor.fetchall()
            counts = {'support': 0, 'oppose': 0, 'neutral': 0}
            for (stance,) in data:
                if stance in counts:
                    counts[stance] += 1
            return [counts['support'], counts['oppose'], counts['neutral']]

        pre_data_sur = get_counts('pre')
        post_data_sur = get_counts('post')

        # Only fetch current user's notes
        cursor.execute("""
            SELECT week, content, created_at FROM notes
            WHERE debate_id = ? AND user_id = ?
        """, (debate_id, user_id))
        notes = cursor.fetchall()

        # User's submitted surveys
        cursor.execute("SELECT comment, stance FROM surveys WHERE user_id = ? AND debate_id = ? AND phase = 'pre'", (user_id, debate_id))
        user_pre_survey = cursor.fetchone()

        cursor.execute("SELECT comment, stance FROM surveys WHERE user_id = ? AND debate_id = ? AND phase = 'post'", (user_id, debate_id))
        user_post_survey = cursor.fetchone()

        cursor.execute("SELECT comment, stance FROM surveys WHERE user_id = ? AND debate_id = ? AND phase = 'week2'", (user_id, debate_id))
        user_mid_survey = cursor.fetchone()

        cursor.execute("SELECT alignment FROM alignment_results WHERE user_id = ? AND debate_id = ?", (user_id, debate_id))
        alignment_result = cursor.fetchone()

        cursor.execute('SELECT alignment FROM alignment_results WHERE user_id=? AND debate_id=? AND phase="pre"', (user_id, debate_id))
        alignment_pre = cursor.fetchone()
        alignment_pre = alignment_pre[0] if alignment_pre else None

        cursor.execute('SELECT alignment FROM alignment_results WHERE user_id=? AND debate_id=? AND phase="post"', (user_id, debate_id))
        alignment_post = cursor.fetchone()
        alignment_post = alignment_post[0] if alignment_post else None

        # Check if user submitted surveys
        def has_submitted(phase):
            cursor.execute("SELECT 1 FROM surveys WHERE user_id = ? AND phase = ? AND debate_id = ?", (user_id, phase, debate_id))
            return cursor.fetchone() is not None

        submitted_week1 = has_submitted('pre')
        submitted_week2 = has_submitted('week2')

        # User's saved notes dict
        saved_notes = {row[0]: row[1] for row in notes}

    # Fetch latest news using News API
    news_articles = fetch_news(topic, debate_id)
    cursor.execute("SELECT central_view FROM debates WHERE id = ?", (debate_id,))
    central_view = cursor.fetchone()[0]
    pre_done, pre_data = check_alignment_completion(user_id, debate_id, "pre")
    post_done, post_data = check_alignment_completion(user_id, debate_id, "post")
    alignment_questions = load_alignment_questions()
    topics = [q['Topic'] for q in alignment_questions]
    group_average = get_mock_group_average(topics)
    return render_template('debate_view.html',
                           topic=topic,
                           country=country,
                           group_average=group_average,
                           pre_data=pre_data,
                           post_data=post_data,
                           date=date,
                           central_view=central_view,
                           saved_notes=saved_notes,
                           pre_data_sur=pre_data_sur,
                           post_data_sur=post_data_sur,
                           notes=notes,
                           debate_id=debate_id,
                           user_pre_survey=user_pre_survey,
                           user_post_survey=user_post_survey,
                           user_mid_survey=user_mid_survey,
                           submitted_week1=submitted_week1,
                           submitted_week2=submitted_week2,
                           alignment_result=alignment_result[0] if alignment_result else None,
                           alignment_pre=alignment_pre,
                           alignment_post=alignment_post,
                           news_articles=news_articles)





if __name__ == '__main__':
    init_db()
    app.run(debug=True,port = 8080)
