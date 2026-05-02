from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DB_FILE = "tasks.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS tasks
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     task TEXT NOT NULL,
                     completed BOOLEAN NOT NULL CHECK (completed IN (0, 1)))''')
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def home():
    error = None
    if request.method == "POST":
        task = request.form.get("task", "").strip()
        if not task:
            error = "Task cannot be empty"
        elif len(task) > 200:
            error = "Task too long (max 200 characters)"
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO tasks (task, completed) VALUES (?, ?)', (task, 0))
            conn.commit()
            conn.close()
            return redirect(url_for("home"))
            
    filter_type = request.args.get('filter', 'all')
    
    conn = get_db_connection()
    if filter_type == 'active':
        tasks = conn.execute('SELECT * FROM tasks WHERE completed = 0').fetchall()
    elif filter_type == 'completed':
        tasks = conn.execute('SELECT * FROM tasks WHERE completed = 1').fetchall()
    else:
        tasks = conn.execute('SELECT * FROM tasks').fetchall()
    conn.close()
    return render_template("index.html", tasks=tasks, current_filter=filter_type, error=error)

@app.route("/edit/<int:task_id>", methods=["POST"])
def edit(task_id):
    new_task = request.form.get("task_text", "").strip()
    if new_task and len(new_task) <= 200:
        conn = get_db_connection()
        task = conn.execute('SELECT id FROM tasks WHERE id = ?', (task_id,)).fetchone()
        if task:
            conn.execute('UPDATE tasks SET task = ? WHERE id = ?', (new_task, task_id))
            conn.commit()
        conn.close()
    return redirect(request.referrer or url_for("home"))

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    conn = get_db_connection()
    task = conn.execute('SELECT id FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if task:
        conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
    conn.close()
    return redirect(request.referrer or url_for("home"))

@app.route("/complete/<int:task_id>", methods=["POST"])
def complete(task_id):
    conn = get_db_connection()
    task = conn.execute('SELECT completed FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if task is not None:
        new_status = 0 if task['completed'] else 1
        conn.execute('UPDATE tasks SET completed = ? WHERE id = ?', (new_status, task_id))
        conn.commit()
    conn.close()
    return redirect(request.referrer or url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
