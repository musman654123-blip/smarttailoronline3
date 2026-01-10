from flask import Flask, request, redirect, session, render_template_string
import sqlite3, os, shutil
from datetime import datetime

# ---------------- CONFIG ----------------
app = Flask(__name__)
app.secret_key = "SMART-TAILOR-SECRET"

DB_FILE = "data.db"
ADMIN_PASSWORD = "admin123"

# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    # Customers
    cur.execute("""
    CREATE TABLE IF NOT EXISTS customers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        mobile TEXT,
        length TEXT,
        chest TEXT,
        waist TEXT,
        shalwar_length TEXT,
        cuff TEXT,
        side TEXT,
        packet TEXT,
        shalwar_packet TEXT,
        zip TEXT,
        ghara TEXT,
        slai TEXT,
        button_style TEXT,
        poncha TEXT,
        collar TEXT,
        amount TEXT,
        created_at TEXT
    )
    """)
    # Licenses
    cur.execute("""
    CREATE TABLE IF NOT EXISTS licenses(
        license TEXT PRIMARY KEY,
        name TEXT,
        status TEXT,
        last_login TEXT,
        last_ip TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- BACKUP ----------------
def backup_db():
    if not os.path.exists("backup"):
        os.mkdir("backup")
    shutil.copy(DB_FILE, f"backup/data_{datetime.now().strftime('%Y%m%d_%H%M')}.db")

# ---------------- LICENSE ----------------
def check_license(code):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM licenses WHERE license=? AND status='active'", (code,))
    res = cur.fetchone()
    conn.close()
    return res is not None

def update_last_login(code, ip=None):
    conn = get_db()
    conn.execute("UPDATE licenses SET last_login=?, last_ip=? WHERE license=?",
                 (datetime.now().strftime("%Y-%m-%d %H:%M"), ip or "", code))
    conn.commit()
    conn.close()

# ---------------- DEMO LICENSE ----------------
def demo_license():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM licenses WHERE license='DEMO123'")
    if not cur.fetchone():
        conn.execute("INSERT INTO licenses VALUES (?,?,?,?,?)", ("DEMO123","Demo Tailor","active","",""))
        conn.commit()
    conn.close()

demo_license()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        code = request.form.get("license")
        if check_license(code):
            session["license"] = code
            update_last_login(code, request.remote_addr)
            return redirect("/dashboard")
        return "<h3 style='color:red'>❌ Invalid or Blocked License</h3>"
    return render_template_string("""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Tailor Login</title>
    </head>
    <body style="font-family:sans-serif;background:#f0f0f0;text-align:center;padding-top:50px;">
        <div style='max-width:400px;margin:auto;padding:20px;border-radius:10px;background:white;box-shadow:0px 0px 10px #aaa'>
        <h2 style='color:#4CAF50'>Smart Tailor Login</h2>
        <form method="post">
            <input name="license" placeholder="Enter License" required style='width:100%;padding:10px;margin:10px 0;border-radius:5px;border:1px solid #ccc;'><br>
            <button style='width:100%;padding:10px;background:#4CAF50;color:white;border:none;border-radius:5px;'>Login</button>
        </form>
        </div>
    </body>
    </html>
    """)

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "license" not in session:
        return redirect("/")
    return render_template_string("""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Tailor Dashboard</title>
    </head>
    <body style="font-family:sans-serif;background:#f0f0f0;padding:20px;">
        <div style="max-width:700px;margin:auto;background:white;padding:20px;border-radius:10px;box-shadow:0 0 10px #aaa;">
        <h2 style="color:#4CAF50">Add Customer</h2>
        <form method="post" action="/add">
          Name: <input name="name" required style="width:100%;padding:8px;margin:5px 0;"><br>
          Mobile: <input name="mobile" required style="width:100%;padding:8px;margin:5px 0;"><br>
          Length: <input name="length" style="width:100%;padding:8px;margin:5px 0;"><br>
          Chest: <input name="chest" style="width:100%;padding:8px;margin:5px 0;"><br>
          Waist: <input name="waist" style="width:100%;padding:8px;margin:5px 0;"><br>
          Shalwar Length: <input name="shalwar_length" style="width:100%;padding:8px;margin:5px 0;"><br>
          Cuff: <input name="cuff" style="width:100%;padding:8px;margin:5px 0;"><br>
          Side: <input name="side" style="width:100%;padding:8px;margin:5px 0;"><br>
          Packet: <input name="packet" style="width:100%;padding:8px;margin:5px 0;"><br>
          Shalwar Packet: <input name="shalwar_packet" style="width:100%;padding:8px;margin:5px 0;"><br>
          Zip: <input name="zip" style="width:100%;padding:8px;margin:5px 0;"><br>
          Ghara: <input name="ghara" style="width:100%;padding:8px;margin:5px 0;"><br>
          Slai: <select name="slai" style="width:100%;padding:8px;margin:5px 0;">
                    <option>Single</option><option>Double</option></select><br>
          Button Style: <select name="button_style" style="width:100%;padding:8px;margin:5px 0;">
                    <option>Fancy</option><option>Simple</option></select><br>
          Poncha: <input name="poncha" style="width:100%;padding:8px;margin:5px 0;"><br>
          Collar: <input name="collar" style="width:100%;padding:8px;margin:5px 0;"><br>
          Amount: <input name="amount" style="width:100%;padding:8px;margin:5px 0;"><br><br>
          <button style="width:100%;padding:10px;background:#4CAF50;color:white;border:none;border-radius:5px;">Save Customer</button>
        </form>
        <br>
        <a href="/view" style="display:inline-block;padding:10px;background:#2196F3;color:white;border-radius:5px;text-decoration:none;">View All Customers</a>
        <a href="/search" style="display:inline-block;padding:10px;background:#FF9800;color:white;border-radius:5px;text-decoration:none;">Search</a>
        <a href="/logout" style="display:inline-block;padding:10px;background:#f44336;color:white;border-radius:5px;text-decoration:none;">Logout</a>
        </div>
    </body>
    </html>
    """)

# ---------------- ADD CUSTOMER ----------------
@app.route("/add", methods=["POST"])
def add():
    if "license" not in session:
        return redirect("/")
    conn = get_db()
    conn.execute("""
    INSERT INTO customers
    (name,mobile,length,chest,waist,shalwar_length,cuff,side,packet,shalwar_packet,zip,ghara,slai,button_style,poncha,collar,amount,created_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        request.form["name"], request.form["mobile"], request.form.get("length"), request.form.get("chest"),
        request.form.get("waist"), request.form.get("shalwar_length"), request.form.get("cuff"),
        request.form.get("side"), request.form.get("packet"), request.form.get("shalwar_packet"),
        request.form.get("zip"), request.form.get("ghara"), request.form.get("slai"),
        request.form.get("button_style"), request.form.get("poncha"), request.form.get("collar"),
        request.form.get("amount"), datetime.now().strftime("%Y-%m-%d %H:%M")
    ))
    conn.commit()
    conn.close()
    backup_db()
    return redirect("/dashboard")

# ---------------- VIEW CUSTOMERS ----------------
@app.route("/view")
def view_customers():
    if "license" not in session:
        return redirect("/")
    conn = get_db()
    rows = conn.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()
    conn.close()
    html = "<h2>All Customers</h2>"
    for r in rows:
        html += f"<pre>{dict(r)}</pre><hr>"
    html += '<a href="/dashboard">Back</a>'
    return html

# ---------------- SEARCH ----------------
@app.route("/search", methods=["GET","POST"])
def search_customers():
    if "license" not in session:
        return redirect("/")
    if request.method=="POST":
        q = request.form.get("query","")
        conn = get_db()
        rows = conn.execute("SELECT * FROM customers WHERE name LIKE ? OR mobile LIKE ?",(f"%{q}%","%{q}%")).fetchall()
        conn.close()
        html = f"<h2>Search results for '{q}'</h2>"
        for r in rows:
            html += f"<pre>{dict(r)}</pre><hr>"
        html += '<a href="/dashboard">Back</a>'
        return html
    return """
    <form method="post">
        Name or Mobile: <input name="query" required>
        <button>Search</button>
    </form>
    """

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- ADMIN ----------------
@app.route("/admin-login", methods=["GET","POST"])
def admin_login():
    if request.method=="POST":
        if request.form.get("password")==ADMIN_PASSWORD:
            session["admin"]=True
            return redirect("/admin")
    return """
    <form method="post">
        <input name="password" placeholder="Admin Password" required>
        <button>Login</button>
    </form>
    """

@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/admin-login")
    conn = get_db()
    licenses = conn.execute("SELECT * FROM licenses").fetchall()
    conn.close()
    html = "<h2>Admin Dashboard</h2>"
    html += "<table border=1 style='border-collapse:collapse'><tr><th>License</th><th>Name</th><th>Status</th><th>Last Login</th><th>Actions</th></tr>"
    for l in licenses:
        html += f"<tr><td>{l['license']}</td><td>{l['name']}</td><td>{l['status']}</td><td>{l['last_login']}</td>"
        html += f"<td><a href='/admin/remove/{l['license']}'>Remove</a></td></tr>"
    html += "</table>"
    html += """
    <h3>Add License</h3>
    <form method='post' action='/admin/add'>
      License: <input name='license' required>
      Name: <input name='name' required>
      <button>Add License</button>
    </form>
    """
    return html

@app.route("/admin/add", methods=["POST"])
def admin_add():
    if not session.get("admin"):
        return redirect("/admin-login")
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO licenses (license,name,status,last_login,last_ip) VALUES (?,?,?,?,?)",
                 (request.form["license"], request.form["name"], "active","",""))
    conn.commit()
    conn.close()
    return redirect("/admin")

@app.route("/admin/remove/<code>")
def admin_remove(code):
    if not session.get("admin"):
        return redirect("/admin-login")
    conn = get_db()
    conn.execute("DELETE FROM licenses WHERE license=?", (code,))
    conn.commit()
    conn.close()
    return redirect("/admin")

# ---------------- RUN ----------------
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=True)