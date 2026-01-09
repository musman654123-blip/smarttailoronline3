from flask import Flask, request, redirect, url_for, render_template_string, session
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "smart-tailor-secret"

DB_FILE = "tailor.db"

# ===================== DATABASE INIT =====================
def init_db():
    # Delete old DB if exists (fixes old column issues)
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Users table
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                 username TEXT PRIMARY KEY,
                 password TEXT,
                 is_admin INTEGER,
                 license_active INTEGER)""")
    # Customers table
    c.execute("""CREATE TABLE IF NOT EXISTS customers (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT,
                 mobile TEXT,
                 length REAL,
                 chest REAL,
                 waist REAL,
                 shoulder REAL,
                 sleeve REAL,
                 packet TEXT,
                 date_added TEXT)""")
    # Add default admin
    c.execute("INSERT INTO users VALUES ('admin','admin123',1,1)")
    conn.commit()
    conn.close()

# ===================== ROUTES =====================

# Login page
@app.route("/", methods=["GET", "POST"])
def login():
    login_page = '''
    <h2>Smart Tailor Login</h2>
    {% if error %}<p style="color:red">{{ error }}</p>{% endif %}
    <form method="post">
      Username: <input type="text" name="username"><br>
      Password: <input type="password" name="password"><br>
      <input type="submit" value="Login">
    </form>
    '''
    error = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT password, is_admin, license_active FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        if user and user[0] == password:
            session["username"] = username
            session["is_admin"] = user[1]
            session["license_active"] = user[2]
            if user[1]:  # admin
                return redirect(url_for("admin_dashboard"))
            else:
                if not user[2]:
                    return "<h3>License Not Activated. Contact Admin.</h3><a href='/'>Back to Login</a>"
                return redirect(url_for("user_dashboard"))
        else:
            error = "Invalid Credentials"
    return render_template_string(login_page, error=error)

# Admin dashboard
# Admin dashboard (updated)
@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    if "username" not in session or not session.get("is_admin"):
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Add new user
    message = ""
    if request.method == "POST":
        if "add_user" in request.form:
            new_username = request.form["new_username"]
            new_password = request.form["new_password"]
            license_active = 1 if request.form.get("license_active") == "on" else 0
            try:
                c.execute("INSERT INTO users VALUES (?,?,0,?)", (new_username, new_password, license_active))
                conn.commit()
                message = f"User '{new_username}' added!"
            except sqlite3.IntegrityError:
                message = "Username already exists!"

        # License activate/deactivate existing users
        action = request.form.get("action")
        user_to_update = request.form.get("user")
        if user_to_update:
            if action == "activate":
                c.execute("UPDATE users SET license_active=1 WHERE username=?", (user_to_update,))
            elif action == "deactivate":
                c.execute("UPDATE users SET license_active=0 WHERE username=?", (user_to_update,))
            conn.commit()

    c.execute("SELECT username, license_active FROM users WHERE is_admin=0")
    licenses = c.fetchall()
    c.execute("SELECT COUNT(*) FROM customers")
    total_customers = c.fetchone()[0]
    conn.close()

    admin_page = '''
    <h2>Admin Dashboard</h2>
    <p>Total Customers: {{ total_customers }}</p>
    {% if message %}<p style="color:green">{{ message }}</p>{% endif %}

    <h3>Add New User</h3>
    <form method="post">
        Username: <input type="text" name="new_username" required>
        Password: <input type="text" name="new_password" required>
        License Active: <input type="checkbox" name="license_active">
        <input type="submit" name="add_user" value="Add User">
    </form>

    <h3>Existing Users Licenses</h3>
    <form method="post">
    <table border=1>
    <tr><th>Username</th><th>Status</th><th>Action</th></tr>
    {% for user, active in licenses %}
    <tr>
      <td>{{ user }}</td>
      <td>{{ "Active" if active else "Inactive" }}</td>
      <td>
        <button name="action" value="activate">Activate</button>
        <button name="action" value="deactivate">Deactivate</button>
        <input type="hidden" name="user" value="{{ user }}">
      </td>
    </tr>
    {% endfor %}
    </table>
    </form>
    <br><a href="{{ url_for('logout') }}">Logout</a>
    '''
    return render_template_string(admin_page, licenses=licenses, total_customers=total_customers, message=message)

# User dashboard
@app.route("/user", methods=["GET", "POST"])
def user_dashboard():
    if "username" not in session or session.get("is_admin"):
        return redirect(url_for("login"))
    username = session["username"]
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    message = ""
    if request.method == "POST":
        name = request.form["name"]
        mobile = request.form["mobile"]
        length = request.form.get("length", 0)
        chest = request.form.get("chest", 0)
        waist = request.form.get("waist", 0)
        shoulder = request.form.get("shoulder", 0)
        sleeve = request.form.get("sleeve", 0)
        packet = request.form.get("packet", "")
        c.execute("INSERT INTO customers (name,mobile,length,chest,waist,shoulder,sleeve,packet,date_added) VALUES (?,?,?,?,?,?,?,?,?)",
                  (name,mobile,length,chest,waist,shoulder,sleeve,packet,str(datetime.now())))
        conn.commit()
        message = "Customer Added!"
    c.execute("SELECT * FROM customers")
    customers = c.fetchall()
    conn.close()

    user_page = '''
    <h2>Welcome {{ username }}</h2>
    {% if message %}<p style="color:green">{{ message }}</p>{% endif %}
    <form method="post">
      Name: <input type="text" name="name" required><br>
      Mobile: <input type="text" name="mobile" required><br>
      Length: <input type="number" name="length"><br>
      Chest: <input type="number" name="chest"><br>
      Waist: <input type="number" name="waist"><br>
      Shoulder: <input type="number" name="shoulder"><br>
      Sleeve: <input type="number" name="sleeve"><br>
      Packet: <input type="text" name="packet"><br>
      <input type="submit" value="Add Customer">
    </form>
    <h3>All Customers</h3>
    <table border=1>
    <tr><th>ID</th><th>Name</th><th>Mobile</th><th>Length</th><th>Chest</th><th>Waist</th><th>Shoulder</th><th>Sleeve</th><th>Packet</th><th>Date</th></tr>
    {% for c in customers %}
    <tr>
    {% for v in c %}<td>{{ v }}</td>{% endfor %}
    </tr>
    {% endfor %}
    </table>
    <br><a href="{{ url_for('logout') }}">Back</a>
    '''
    return render_template_string(user_page, username=username, customers=customers, message=message)

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ===================== MAIN =====================
if __name__ == "__main__":
    init_db()
    app.run(debug=True)