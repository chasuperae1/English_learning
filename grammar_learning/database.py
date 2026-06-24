import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'grammar.db')


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            category TEXT,
            content TEXT NOT NULL,
            examples TEXT,
            mastery_level INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            last_reviewed_at TEXT,
            review_count INTEGER DEFAULT 0,
            ielts_relevant BOOLEAN DEFAULT 1
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mistakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            your_answer TEXT,
            correct_answer TEXT,
            knowledge_point_id INTEGER,
            mistake_type TEXT,
            reason TEXT,
            created_at TEXT NOT NULL,
            reviewed BOOLEAN DEFAULT 0,
            review_count INTEGER DEFAULT 0,
            last_reviewed_at TEXT,
            FOREIGN KEY (knowledge_point_id) REFERENCES knowledge_points(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS review_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            knowledge_point_id INTEGER,
            mistake_id INTEGER,
            scheduled_date TEXT NOT NULL,
            review_type TEXT NOT NULL,
            completed BOOLEAN DEFAULT 0,
            completed_at TEXT,
            FOREIGN KEY (knowledge_point_id) REFERENCES knowledge_points(id),
            FOREIGN KEY (mistake_id) REFERENCES mistakes(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_name TEXT NOT NULL,
            target_score REAL,
            current_level TEXT,
            start_date TEXT NOT NULL,
            target_date TEXT,
            description TEXT,
            achieved BOOLEAN DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            duration_minutes INTEGER,
            topics_covered TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        )
    ''')

    cursor.execute('SELECT COUNT(*) FROM study_goals')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO study_goals (goal_name, target_score, current_level, start_date, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            '雅思总分 7.0',
            7.0,
            'Beginner',
            datetime.now().strftime('%Y-%m-%d'),
            '雅思四个单项均达到 7 分以上'
        ))

    conn.commit()
    conn.close()
