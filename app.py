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
UPLOAD_FOLDER = 'static/debate_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alignment_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                debate_id INTEGER,
                phase TEXT,  -- 'pre' or 'post'
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

        # Survey visibility
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS survey_visibility (
                phase TEXT PRIMARY KEY,
                visible INTEGER DEFAULT 0
            )
        ''')

        # ✅ ADD THIS: Notes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                week TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert default debates if none
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
        raw_date = request.form['date']  # e.g. '20250520'
        date = f"{raw_date[:4]}.{raw_date[4:6]}.{raw_date[6:]}"  # '2025.05.20'

        image = request.files.get('image')
        image_filename = None

        if image and image.filename:
            image_filename = f"{topic.replace(' ', '_')}_{random.randint(1000, 9999)}.png"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("ALTER TABLE debates ADD COLUMN image TEXT")  # safe to retry
            cursor.execute(
                "INSERT INTO debates (topic, country, date, is_active, image) VALUES (?, ?, ?, ?, ?)",
                (topic, country, date, 1, image_filename)
            )
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
@app.route('/save-alignment/<int:debate_id>', methods=['POST'])
def save_alignment(debate_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user_id']
    data = request.get_json()
    alignment = data.get('alignment')
    phase = data.get('phase')  # 'pre' or 'post'

    if phase not in ('pre', 'post'):
        return jsonify({'error': 'Invalid phase'}), 400

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO alignment_results (user_id, debate_id, phase, alignment)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, debate_id, phase) DO UPDATE SET alignment=excluded.alignment
        ''', (user_id, debate_id, phase, alignment))
        conn.commit()

    return jsonify({'status': 'saved'})


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
            SELECT d.id, d.topic
            FROM debates d
            JOIN surveys s ON d.id = s.debate_id
            WHERE s.user_id = ?
            GROUP BY d.id
        ''', (user_id,))
        debates = cursor.fetchall()

        debate_details = {}
        for debate_id, topic in debates:
            # Get pre and post survey data
            cursor.execute('''
                SELECT stance, comment FROM surveys
                WHERE user_id = ? AND debate_id = ? AND phase = 'pre'
            ''', (user_id, debate_id))
            pre = cursor.fetchone()

            cursor.execute('''
                SELECT stance, comment FROM surveys
                WHERE user_id = ? AND debate_id = ? AND phase = 'post'
            ''', (user_id, debate_id))
            post = cursor.fetchone()

            # Get alignment results
            cursor.execute('''
                SELECT alignment FROM alignment_results
                WHERE user_id = ? AND debate_id = ? AND phase = 'pre'
            ''', (user_id, debate_id))
            align_pre = cursor.fetchone()

            cursor.execute('''
                SELECT alignment FROM alignment_results
                WHERE user_id = ? AND debate_id = ? AND phase = 'post'
            ''', (user_id, debate_id))
            align_post = cursor.fetchone()

            debate_details[topic] = {
                'pre_stance': pre[0] if pre else None,
                'pre_comment': pre[1] if pre else None,
                'post_stance': post[0] if post else None,
                'post_comment': post[1] if post else None,
                'alignment_pre': align_pre[0] if align_pre else None,
                'alignment_post': align_post[0] if align_post else None,
            }

    return render_template("mypage.html", username=username, debate_details=debate_details)


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



@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('index'))
@app.route('/debate/<int:debate_id>')
def debate(debate_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    username = session['username']
    assigned_side = session.get(f'side_{debate_id}')
    if not assigned_side:
        assigned_side = random.choice(['left', 'right'])
        session[f'side_{debate_id}'] = assigned_side

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT topic, country, date FROM debates WHERE id = ?", (debate_id,))
        debate = cursor.fetchone()
        if not debate:
            flash("Debate not found.")
            return redirect(url_for('dashboard'))

        topic, country, date = debate

        def count_stances(phase):
            cursor.execute("SELECT stance FROM surveys WHERE phase = ? AND debate_id = ?", (phase, debate_id))
            data = cursor.fetchall()
            counts = {'support': 0, 'oppose': 0, 'neutral': 0}
            for (stance,) in data:
                if stance in counts:
                    counts[stance] += 1
            return counts

        def has_submitted(phase):
            cursor.execute("SELECT 1 FROM surveys WHERE user_id = ? AND phase = ? AND debate_id = ?",
                           (user_id, phase, debate_id))
            return cursor.fetchone() is not None

        pre = count_stances('pre')
        post = count_stances('post')
        pre_submitted = has_submitted('pre')
        post_submitted = has_submitted('post')

    user_display = f"{username} ({username}@email.com)"
    left_group = ['ADMIN KIM (admin@admin.com)']
    right_group = ['ADMIN KIM (admin@admin.com)']
    if assigned_side == 'left':
        left_group.append(user_display)
    else:
        right_group.append(user_display)
    cursor.execute('SELECT alignment FROM alignment_results WHERE user_id=? AND debate_id=? AND phase="pre"',
                   (user_id, debate_id))
    alignment_pre = cursor.fetchone()
    alignment_pre = alignment_pre[0] if alignment_pre else None

    cursor.execute('SELECT alignment FROM alignment_results WHERE user_id=? AND debate_id=? AND phase="post"',
                   (user_id, debate_id))
    alignment_post = cursor.fetchone()
    alignment_post = alignment_post[0] if alignment_post else None

    return render_template('debate.html',
                           topic=topic,
                           country=country,
                           date=date,
                           left_group=left_group,
                           right_group=right_group,
                           pre_data=list(pre.values()),
                           post_data=list(post.values()),
                           pre_submitted=pre_submitted,
                           post_submitted=post_submitted,
                           debate_id=debate_id,
                           alignment_pre=alignment_pre,
                           alignment_post=alignment_post)

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

        # Pre/Post Survey Results (All)
        def get_counts(phase):
            cursor.execute("SELECT stance FROM surveys WHERE debate_id = ? AND phase = ?", (debate_id, phase))
            data = cursor.fetchall()
            counts = {'support': 0, 'oppose': 0, 'neutral': 0}
            for (stance,) in data:
                if stance in counts:
                    counts[stance] += 1
            return [counts['support'], counts['oppose'], counts['neutral']]

        pre_data = get_counts('pre')
        post_data = get_counts('post')

        # Notes
        cursor.execute("SELECT user_id, content, created_at FROM notes WHERE week IN ('week1', 'week2', 'week3') AND user_id IN (SELECT user_id FROM surveys WHERE debate_id = ?)", (debate_id,))
        notes = cursor.fetchall()

        # ✅ Fetch user's submitted surveys
        cursor.execute("SELECT comment, stance FROM surveys WHERE user_id = ? AND debate_id = ? AND phase = 'pre'", (user_id, debate_id))
        user_pre_survey = cursor.fetchone()

        cursor.execute("SELECT comment, stance FROM surveys WHERE user_id = ? AND debate_id = ? AND phase = 'post'", (user_id, debate_id))
        user_post_survey = cursor.fetchone()
        cursor.execute('''
            SELECT alignment FROM alignment_results WHERE user_id = ? AND debate_id = ?
        ''', (user_id, debate_id))
        alignment_result = cursor.fetchone()
        cursor.execute('SELECT alignment FROM alignment_results WHERE user_id=? AND debate_id=? AND phase="pre"',
                       (user_id, debate_id))
        alignment_pre = cursor.fetchone()
        alignment_pre = alignment_pre[0] if alignment_pre else None

        cursor.execute('SELECT alignment FROM alignment_results WHERE user_id=? AND debate_id=? AND phase="post"',
                       (user_id, debate_id))
        alignment_post = cursor.fetchone()
        alignment_post = alignment_post[0] if alignment_post else None
    return render_template('debate_view.html',
                           topic=topic,
                           country=country,
                           date=date,
                           pre_data=pre_data,
                           post_data=post_data,
                           notes=notes,
                           debate_id=debate_id,
                           user_pre_survey=user_pre_survey,
                           user_post_survey=user_post_survey,
                           alignment_result=alignment_result[0] if alignment_result else None,
                           alignment_pre=alignment_pre,
                           alignment_post=alignment_post)



if __name__ == '__main__':
    init_db()
    app.run(debug=True)
