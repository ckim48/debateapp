import sqlite3
DB_PATH = 'biasbridge.db'
def insert_mock_surveys_for_debate1_and_2():
    mock_data = [
        # Debate ID 1: Gun Control Legislation
        (1, 'pre', 'support', 'Stricter laws save lives.', 1),
        (2, 'pre', 'oppose', 'People need self-defense.', 1),
        (3, 'pre', 'neutral', 'Both sides make good points.', 1),
        (1, 'post', 'support', 'I’m even more in favor now.', 1),
        (2, 'post', 'oppose', 'Still firmly against it.', 1),
        (3, 'post', 'neutral', 'Still unsure.', 1),

        # Debate ID 2: Forgiving student loan debt
        (1, 'pre', 'support', 'Helps reduce inequality.', 2),
        (2, 'pre', 'oppose', 'Tax burden is too high.', 2),
        (3, 'pre', 'support', 'Good for the economy.', 2),
        (1, 'post', 'support', 'Strongly believe in it.', 2),
        (2, 'post', 'oppose', 'No change in opinion.', 2),
        (3, 'post', 'support', 'Now even more supportive.', 2),
    ]

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for user_id, phase, stance, comment, debate_id in mock_data:
            cursor.execute('''
                INSERT INTO surveys (user_id, phase, stance, comment, debate_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, phase, stance, comment, debate_id))
        conn.commit()
    print("Mock survey data for debate ID 1 and 2 inserted.")

insert_mock_surveys_for_debate1_and_2()