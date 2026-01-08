from flask import Flask, render_template, request, redirect
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "smart-tailor-secret"

# =========================
# DATABASE INIT FUNCTION
# =========================
def init_db():
    con = sqlite3.connect("tailor.db")
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        length TEXT,
        chest TEXT,
        waist TEXT,
        shoulder TEXT,
        sleeve TEXT,
        collar TEXT,
        front TEXT,
        back TEXT,
        pocket TEXT,
        cuff TEXT,
        plate TEXT,
        button TEXT,
        note TEXT,
        date TEXT
    )
    """)
    con.commit()
    con.close()

# ✅ NOW CALL IT (AFTER DEFINITION)
init_db()

# ================= CONFIG =================
app = Flask(__name__)
app.secret_key = "SMART-TAILOR-SECURE-KEY"

DB_FILE = "data.db"
ADMIN_PASSWORD = "admin123"

# ================= DATABASE =================
def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS customers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        mobile TEXT,
        length TEXT,
        chest TEXT,
        waist TEXT,
        shoulder TEXT,
        sleeve TEXT,
        collar TEXT,
        poncha TEXT,
        batton TEXT,
        packet TEXT,
        zip TEXT,
        shalwar TEXT,
        ghara TEXT,
        amount TEXT,
        note TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS licenses(
        license TEXT PRIMARY KEY,
        name TEXT,
        status TEXT,
        last_login TEXT,
        last_ip TEXT
    )
    """)

    con.commit()
    con.close()

init_db()

# ================= BACKUP =================
def backup():
    if not os.path.exists("backup"):
        os.mkdir("backup")
    shutil.copy(DB_FILE, f"backup/data_{datetime.now().strftime('%Y%m%d_%H%M')}.db")

# ================= LICENSE =================
def valid_license(code):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM licenses WHERE license=? AND status='active'", (code,))
    ok = cur.fetchone()
    con.close()
    return ok

def update_license(code, ip):
    con = db()
    con.execute("UPDATE licenses SET last_login=?, last_ip=? WHERE license=?",
                (datetime.now().strftime("%Y-%m-%d %H:%M"), ip, code))
    con.commit()
    con.close()

# ================= DEMO LICENSE =================
def demo():
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM licenses WHERE license='DEMO123'")
    if not cur.fetchone():
        con.execute("INSERT INTO licenses VALUES (?,?,?,?,?)",
                    ("DEMO123", "Demo Tailor", "active", "", ""))
        con.commit()
    con.close()

demo()

# ================= LOGIN =================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        code = request.form["license"]
        if valid_license(code):
            session["license"] = code
            update_license(code, request.remote_addr)
            return redirect("/dashboard")
        return "<h3 style='color:red'>Invalid License</h3>"

    return """
    <h2>Smart Tailor Login</h2>
    <form method="post">
      <input name="license" placeholder="Enter License" required>
      <button>Login</button>
    </form>
    """

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "license" not in session:
        return redirect("/")
    return """
    <h2>Add Customer</h2>
    <form method="post" action="/add">
      Name <input name="name" required><br>
      Mobile <input name="mobile" required><br>
      Length <input name="length"><br>
      Chest <input name="chest"><br>
      Waist <input name="waist"><br>
      Shoulder <input name="shoulder"><br>
      Sleeve <input name="sleeve"><br>
      Collar <input name="collar"><br>
      Poncha <input name="poncha"><br>
      Batton <input name="batton"><br>
      Packet <input name="packet"><br>
      Zip <input name="zip"><br>
      Shalwar <input name="shalwar"><br>
      Ghara <input name="ghara"><br>
      Amount <input name="amount"><br>
      Note <input name="note"><br><br>
      <button>Save</button>
    </form>

    <h3>Search</h3>
    <form method="get" action="/search">
      <input name="q">
      <button>Search</button>
    </form>

    <br>
    <a href="/customers">View All</a> |
    <a href="/logout">Logout</a>
    """

# ================= ADD CUSTOMER =================
@app.route("/add", methods=["POST"])
def add():
    if "license" not in session:
        return redirect("/")

    con = db()
    con.execute("""
    INSERT INTO customers VALUES
    (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        request.form["name"],
        request.form["mobile"],
        request.form.get("length"),
        request.form.get("chest"),
        request.form.get("waist"),
        request.form.get("shoulder"),
        request.form.get("sleeve"),
        request.form.get("collar"),
        request.form.get("poncha"),
        request.form.get("batton"),
        request.form.get("packet"),
        request.form.get("zip"),
        request.form.get("shalwar"),
        request.form.get("ghara"),
        request.form.get("amount"),
        request.form.get("note"),
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ))
    con.commit()
    con.close()
    backup()
    return redirect("/dashboard")

# ================= SEARCH =================
@app.route("/search")
def search():
    if "license" not in session:
        return redirect("/")

    q = request.args.get("q","")
    con = db()
    rows = con.execute("SELECT * FROM customers WHERE name LIKE ? OR mobile LIKE ?",
                       (f"%{q}%", f"%{q}%")).fetchall()
    con.close()

    out = "<h2>Results</h2>"
    for r in rows:
        out += f"<pre>{dict(r)}</pre><hr>"
    out += "<a href='/dashboard'>Back</a>"
    return out

# ================= LIST =================
@app.route("/customers")
def customers():
    if "license" not in session:
        return redirect("/")

    con = db()
    rows = con.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()
    con.close()

    out = "<h2>All Customers</h2>"
    for r in rows:
        out += f"<pre>{dict(r)}</pre><hr>"
    return out

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= ADMIN =================
@app.route("/admin-login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
    return "<form method='post'><input name='password'><button>Login</button></form>"

@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/admin-login")
    con = db()
    rows = con.execute("SELECT * FROM licenses").fetchall()
    con.close()

    out = "<h2>Admin Panel</h2>"
    for r in rows:
        out += f"{r['license']} | {r['status']} | {r['last_login']}<br>"
    out += """
    <h3>Add License</h3>
    <form method='post' action='/admin-add'>
      <input name='license'>
      <input name='name'>
      <button>Add</button>
    </form>
    """
    return out

@app.route("/admin-add", methods=["POST"])
def admin_add():
    if not session.get("admin"):
        return redirect("/admin-login")
    con = db()
    con.execute("INSERT OR REPLACE INTO licenses VALUES (?,?,?,?,?)",
                (request.form["license"], request.form["name"], "active", "", ""))
    con.commit()
    con.close()
    return redirect("/admin")

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))