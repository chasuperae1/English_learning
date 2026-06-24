from datetime import datetime, timedelta
from .database import get_connection


def add_knowledge_point(topic, content, category=None, examples=None, ielts_relevant=True):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO knowledge_points (topic, category, content, examples, created_at, ielts_relevant)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (topic, category, content, examples, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ielts_relevant))
    conn.commit()
    kp_id = cursor.lastrowid
    conn.close()
    return kp_id


def get_knowledge_point(kp_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM knowledge_points WHERE id = ?', (kp_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def list_knowledge_points(category=None, mastery_level=None, ielts_only=False, limit=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = 'SELECT * FROM knowledge_points WHERE 1=1'
    params = []
    if category:
        query += ' AND category = ?'
        params.append(category)
    if mastery_level is not None:
        query += ' AND mastery_level = ?'
        params.append(mastery_level)
    if ielts_only:
        query += ' AND ielts_relevant = 1'
    query += ' ORDER BY created_at DESC'
    if limit:
        query += ' LIMIT ?'
        params.append(limit)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_mastery_level(kp_id, mastery_level):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE knowledge_points 
        SET mastery_level = ?, last_reviewed_at = ?, review_count = review_count + 1
        WHERE id = ?
    ''', (mastery_level, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), kp_id))
    conn.commit()
    conn.close()


def get_categories():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT category FROM knowledge_points WHERE category IS NOT NULL')
    rows = cursor.fetchall()
    conn.close()
    return [row['category'] for row in rows]


def get_knowledge_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM knowledge_points')
    total = cursor.fetchone()['total']
    cursor.execute('''
        SELECT mastery_level, COUNT(*) as count 
        FROM knowledge_points 
        GROUP BY mastery_level 
        ORDER BY mastery_level
    ''')
    mastery_dist = cursor.fetchall()
    conn.close()
    return {
        'total': total,
        'mastery_distribution': [dict(row) for row in mastery_dist]
    }


def search_knowledge(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM knowledge_points 
        WHERE topic LIKE ? OR content LIKE ? OR examples LIKE ?
        ORDER BY created_at DESC
    ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
