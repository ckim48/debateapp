import sqlite3
import random

DB_PATH = 'biasbridge.db'

def add_mock_closed_debates():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM debates WHERE is_active = 0")
        if cursor.fetchone()[0] == 0:
            closed_debates = [
                ("Climate Change Policy", "South Korea", "2024.11.12"),
                ("Raising the Minimum Wage", "South Korea", "2024.10.30"),
                ("Banning Facial Recognition Tech", "South Korea", "2024.09.18")
            ]
            cursor.executemany(
                "INSERT INTO debates (topic, country, date, is_active) VALUES (?, ?, ?, 0)",
                closed_debates
            )
            conn.commit()
            print("✅ Closed debates added.")
        else:
            print("ℹ️ Closed debates already exist.")

def generate_mock_surveys():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Ensure alignment_results table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alignment_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                debate_id INTEGER,
                alignment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Ensure user_debate_roles table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_debate_roles (
                user_id INTEGER,
                debate_id INTEGER,
                side TEXT CHECK(side IN ('support', 'oppose')),
                PRIMARY KEY (user_id, debate_id)
            )
        ''')

        # Create mock users
        for i in range(1, 6):
            username = f"user{i}@mock.com"
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, 'testpass'))

        # Ensure admin user exists
        cursor.execute("SELECT id FROM users WHERE username = 'test@test.com'")
        admin = cursor.fetchone()
        if not admin:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('test@test.com', 'adminpass'))
            conn.commit()
            cursor.execute("SELECT id FROM users WHERE username = 'test@test.com'")
            admin = cursor.fetchone()
        admin_user_id = admin[0]

        conn.commit()

        # Fetch user IDs
        cursor.execute("SELECT id FROM users WHERE username LIKE 'user%@mock.com'")
        user_ids = [row[0] for row in cursor.fetchall()]

        # Get closed debate IDs
        cursor.execute("SELECT id FROM debates WHERE is_active = 0")
        closed_debates = [row[0] for row in cursor.fetchall()]
        if not closed_debates:
            print("❌ No closed debates found. Run add_mock_closed_debates() first.")
            return

        stances = ['support', 'oppose', 'neutral']
        alignments = ['left', 'center', 'right']
        sides = ['support', 'oppose']

        for debate_id in closed_debates:
            for user_id in user_ids:
                # Pre-survey
                cursor.execute('''
                    INSERT INTO surveys (user_id, phase, stance, comment, debate_id)
                    VALUES (?, 'pre', ?, ?, ?)
                ''', (user_id, random.choice(stances), "This is my initial opinion.", debate_id))

                # Post-survey
                cursor.execute('''
                    INSERT INTO surveys (user_id, phase, stance, comment, debate_id)
                    VALUES (?, 'post', ?, ?, ?)
                ''', (user_id, random.choice(stances), "After hearing arguments, this is what I think.", debate_id))

                # Alignment
                cursor.execute('''
                    INSERT INTO alignment_results (user_id, debate_id, alignment)
                    VALUES (?, ?, ?)
                ''', (user_id, debate_id, random.choice(alignments)))

                # Role assignment
                cursor.execute('''
                    INSERT OR IGNORE INTO user_debate_roles (user_id, debate_id, side)
                    VALUES (?, ?, ?)
                ''', (user_id, debate_id, random.choice(sides)))

            # Admin's surveys and alignment
            cursor.execute('''
                INSERT INTO surveys (user_id, phase, stance, comment, debate_id)
                VALUES (?, 'pre', ?, ?, ?)
            ''', (admin_user_id, random.choice(stances), "Admin's pre-debate opinion.", debate_id))

            cursor.execute('''
                INSERT INTO surveys (user_id, phase, stance, comment, debate_id)
                VALUES (?, 'post', ?, ?, ?)
            ''', (admin_user_id, random.choice(stances), "Admin's post-debate reflection.", debate_id))

            cursor.execute('''
                INSERT INTO alignment_results (user_id, debate_id, alignment)
                VALUES (?, ?, ?)
            ''', (admin_user_id, debate_id, random.choice(alignments)))

            cursor.execute('''
                INSERT OR IGNORE INTO user_debate_roles (user_id, debate_id, side)
                VALUES (?, ?, ?)
            ''', (admin_user_id, debate_id, random.choice(sides)))

        conn.commit()
        print("✅ Mock survey, alignment, and role assignment data inserted.")

def setup_demo_data():
    add_mock_closed_debates()
    generate_mock_surveys()

if __name__ == '__main__':
    setup_demo_data()
