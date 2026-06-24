from datetime import datetime, timedelta
from .database import get_connection
from .knowledge import get_knowledge_point


def schedule_review(knowledge_point_id=None, mistake_id=None, scheduled_date=None, review_type='spaced'):
    if knowledge_point_id is None and mistake_id is None:
        raise ValueError('Must provide either knowledge_point_id or mistake_id')
    if scheduled_date is None:
        scheduled_date = datetime.now().strftime('%Y-%m-%d')
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO review_schedules (knowledge_point_id, mistake_id, scheduled_date, review_type)
        VALUES (?, ?, ?, ?)
    ''', (knowledge_point_id, mistake_id, scheduled_date, review_type))
    conn.commit()
    schedule_id = cursor.lastrowid
    conn.close()
    return schedule_id


def schedule_spaced_review(knowledge_point_id, mastery_level):
    intervals = {
        0: 1,
        1: 2,
        2: 4,
        3: 7,
        4: 14,
        5: 30
    }
    days = intervals.get(mastery_level, 7)
    next_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    return schedule_review(knowledge_point_id=knowledge_point_id,
                           scheduled_date=next_date,
                           review_type=f'spaced_level_{mastery_level}')


def get_today_reviews():
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT rs.*, kp.topic as kp_topic, kp.content as kp_content,
               m.question as mistake_question, m.your_answer, m.correct_answer
        FROM review_schedules rs
        LEFT JOIN knowledge_points kp ON rs.knowledge_point_id = kp.id
        LEFT JOIN mistakes m ON rs.mistake_id = m.id
        WHERE rs.scheduled_date = ? AND rs.completed = 0
        ORDER BY rs.scheduled_date
    ''', (today,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_upcoming_reviews(days=7):
    today = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT rs.*, kp.topic as kp_topic
        FROM review_schedules rs
        LEFT JOIN knowledge_points kp ON rs.knowledge_point_id = kp.id
        WHERE rs.scheduled_date BETWEEN ? AND ? AND rs.completed = 0
        ORDER BY rs.scheduled_date
    ''', (today, end_date))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def complete_review(schedule_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE review_schedules 
        SET completed = 1, completed_at = ?
        WHERE id = ?
    ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), schedule_id))
    conn.commit()
    conn.close()


def add_study_session(duration_minutes, topics_covered=None, notes=None):
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        INSERT INTO study_sessions (date, duration_minutes, topics_covered, notes, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (today, duration_minutes, topics_covered, notes,
          datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id


def get_study_stats(days=30):
    conn = get_connection()
    cursor = conn.cursor()

    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT date, SUM(duration_minutes) as total_minutes, COUNT(*) as sessions
        FROM study_sessions
        WHERE date >= ?
        GROUP BY date
        ORDER BY date DESC
    ''', (start_date,))
    daily_stats = cursor.fetchall()

    cursor.execute('''
        SELECT COUNT(*) as total_sessions, 
               SUM(duration_minutes) as total_minutes,
               AVG(duration_minutes) as avg_minutes
        FROM study_sessions
        WHERE date >= ?
    ''', (start_date,))
    summary = cursor.fetchone()

    cursor.execute('SELECT * FROM study_goals ORDER BY id LIMIT 1')
    goal = cursor.fetchone()

    conn.close()
    return {
        'daily_stats': [dict(row) for row in daily_stats],
        'summary': dict(summary) if summary else None,
        'goal': dict(goal) if goal else None
    }


def get_overall_progress():
    from .knowledge import get_knowledge_stats
    from .mistakes import get_mistake_stats

    k_stats = get_knowledge_stats()
    m_stats = get_mistake_stats()
    study_stats = get_study_stats(30)

    total_mastered = sum(
        item['count'] for item in k_stats['mastery_distribution']
        if item['mastery_level'] >= 4
    )

    return {
        'knowledge_points_total': k_stats['total'],
        'knowledge_mastered': total_mastered,
        'mastery_percentage': round(total_mastered / k_stats['total'] * 100, 1) if k_stats['total'] > 0 else 0,
        'mistakes_total': m_stats['total'],
        'mistakes_unreviewed': m_stats['unreviewed'],
        'study_minutes_30d': study_stats['summary']['total_minutes'] if study_stats['summary'] else 0,
        'goal': study_stats['goal']
    }
