import sqlite3
import pandas as pd


def init_db():
    conn = sqlite3.connect('fitness_progress.db')
    cursor = conn.cursor()

    cursor.execute(
        'CREATE TABLE IF NOT EXISTS exercises (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)')

    cursor.execute(
        'CREATE TABLE IF NOT EXISTS training_days (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS day_exercises (
            day_id INTEGER,
            exercise_id INTEGER,
            FOREIGN KEY (day_id) REFERENCES training_days (id),
            FOREIGN KEY (exercise_id) REFERENCES exercises (id),
            PRIMARY KEY (day_id, exercise_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise_id INTEGER,
            weight REAL,
            reps INTEGER,
            date DATE DEFAULT (DATE('now')),
            FOREIGN KEY (exercise_id) REFERENCES exercises (id)
        )
    ''')
    conn.commit()
    conn.close()


def add_exercise(name):
    conn = sqlite3.connect('fitness_progress.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO exercises (name) VALUES (?)', (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()


def get_exercises():
    conn = sqlite3.connect('fitness_progress.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM exercises')
    data = [row[0] for row in cursor.fetchall()]
    conn.close()
    return data


def save_log(exercise_name, weight, reps, log_date):
    conn = sqlite3.connect('fitness_progress.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM exercises WHERE name = ?', (exercise_name,))
    exercise_id = cursor.fetchone()[0]

    cursor.execute('''
        INSERT INTO logs (exercise_id, weight, reps, date) 
        VALUES (?, ?, ?, ?)
    ''', (exercise_id, weight, reps, log_date))

    conn.commit()
    conn.close()


def get_logs_df(exercise_name):
    conn = sqlite3.connect('fitness_progress.db')
    query = '''
        SELECT l.id, l.date, l.weight, l.reps 
        FROM logs l
        JOIN exercises e ON l.exercise_id = e.id
        WHERE e.name = ?
        ORDER BY l.date DESC, l.id DESC
    '''
    df = pd.read_sql_query(query, conn, params=(exercise_name,))
    conn.close()
    return df


def add_training_day(name):
    conn = sqlite3.connect('fitness_progress.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO training_days (name) VALUES (?)', (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()


def get_training_days():
    conn = sqlite3.connect('fitness_progress.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM training_days')
    days = [row[0] for row in cursor.fetchall()]
    conn.close()
    return days


def link_exercise_to_day(day_name, exercise_name):
    conn = sqlite3.connect('fitness_progress.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM training_days WHERE name = ?', (day_name,))
    d_id = cursor.fetchone()[0]
    cursor.execute('SELECT id FROM exercises WHERE name = ?', (exercise_name,))
    e_id = cursor.fetchone()[0]

    cursor.execute('INSERT OR IGNORE INTO day_exercises (day_id, exercise_id) VALUES (?, ?)', (d_id, e_id))
    conn.commit()
    conn.close()


def get_exercises_by_day(day_name):
    conn = sqlite3.connect('fitness_progress.db')
    cursor = conn.cursor()
    query = '''
        SELECT e.name FROM exercises e
        JOIN day_exercises de ON e.id = de.exercise_id
        JOIN training_days td ON de.day_id = td.id
        WHERE td.name = ?
    '''
    cursor.execute(query, (day_name,))
    exercises = [row[0] for row in cursor.fetchall()]
    conn.close()
    return exercises


def delete_log(log_id):
    conn = sqlite3.connect('fitness_progress.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM logs WHERE id = ?', (log_id,))
    conn.commit()
    conn.close()


def remove_exercise_from_day(day_name, exercise_name):
    conn = sqlite3.connect('fitness_progress.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM training_days WHERE name = ?', (day_name,))
    d_id = cursor.fetchone()[0]
    cursor.execute('SELECT id FROM exercises WHERE name = ?', (exercise_name,))
    e_id = cursor.fetchone()[0]

    cursor.execute('DELETE FROM day_exercises WHERE day_id = ? AND exercise_id = ?', (d_id, e_id))
    conn.commit()
    conn.close()


def get_all_logs_df():
    import pandas as pd
    conn = sqlite3.connect('fitness_progress.db')
    query = '''
        SELECT 
            l.date, 
            td.name as training_day, 
            e.name as exercise, 
            l.weight, 
            l.reps 
        FROM logs l
        JOIN exercises e ON l.exercise_id = e.id
        LEFT JOIN day_exercises de ON e.id = de.exercise_id
        LEFT JOIN training_days td ON de.day_id = td.id
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
