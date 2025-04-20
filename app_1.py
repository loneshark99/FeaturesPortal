from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__, 
            template_folder='task_manager/templates',
            static_folder='task_manager/static')
app.secret_key = "your_secret_key"

# Database initialization
def init_db():
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'pending'
    )
    ''')
    conn.commit()
    conn.close()

# Initialize the database on startup
init_db()

# Helper function to get database connection
def get_db_connection():
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row
    return conn

# Routes
@app.route('/')
def index():
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks').fetchall()
    conn.close()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    title = request.form['title']
    description = request.form['description']
    status = request.form['status']
    
    if not title:
        flash('Title is required!')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    conn.execute('INSERT INTO tasks (title, description, status) VALUES (?, ?, ?)',
                 (title, description, status))
    conn.commit()
    conn.close()
    flash('Task added successfully!')
    return redirect(url_for('index'))

@app.route('/update/<int:id>', methods=['POST'])
def update_task(id):
    title = request.form['title']
    description = request.form['description']
    status = request.form['status']
    
    if not title:
        flash('Title is required!')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    conn.execute('UPDATE tasks SET title = ?, description = ?, status = ? WHERE id = ?',
                 (title, description, status, id))
    conn.commit()
    conn.close()
    flash('Task updated successfully!')
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_task(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tasks WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Task deleted successfully!')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)