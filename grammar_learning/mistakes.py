from datetime import datetime
from .database import get_connection


def add_mistake(question, your_answer=None, correct_answer=None, knowledge_point_id=None,
                mistake_type=None, reason=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO mistakes (question, your_answer, correct_answer, knowledge_point_id, 
                              mistake_type, reason, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (question, your_answer, correct_answer, knowledge_point_id,
          mistake_type, reason, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    mistake_id = cursor.lastrowid
    conn.close()
    return mistake_id


def get_mistake(mistake_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM mistakes WHERE id = ?', (mistake_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def list_mistakes(reviewed=None, mistake_type=None, knowledge_point_id=None, limit=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = 'SELECT * FROM mistakes WHERE 1=1'
    params = []
    if reviewed is not None:
        query += ' AND reviewed = ?'
        params.append(1 if reviewed else 0)
    if mistake_type:
        query += ' AND mistake_type = ?'
        params.append(mistake_type)
    if knowledge_point_id:
        query += ' AND knowledge_point_id = ?'
        params.append(knowledge_point_id)
    query += ' ORDER BY created_at DESC'
    if limit:
        query += ' LIMIT ?'
        params.append(limit)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_mistake_reviewed(mistake_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE mistakes 
        SET reviewed = 1, review_count = review_count + 1, last_reviewed_at = ?
        WHERE id = ?
    ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), mistake_id))
    conn.commit()
    conn.close()


def get_mistake_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM mistakes')
    total = cursor.fetchone()['total']
    cursor.execute('SELECT COUNT(*) as unreviewed FROM mistakes WHERE reviewed = 0')
    unreviewed = cursor.fetchone()['unreviewed']
    cursor.execute('''
        SELECT mistake_type, COUNT(*) as count 
        FROM mistakes 
        WHERE mistake_type IS NOT NULL
        GROUP BY mistake_type 
        ORDER BY count DESC
    ''')
    type_dist = cursor.fetchall()
    conn.close()
    return {
        'total': total,
        'unreviewed': unreviewed,
        'type_distribution': [dict(row) for row in type_dist]
    }


def get_mistake_types():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT mistake_type FROM mistakes WHERE mistake_type IS NOT NULL')
    rows = cursor.fetchall()
    conn.close()
    return [row['mistake_type'] for row in rows]
