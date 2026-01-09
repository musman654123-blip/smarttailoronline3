from flask import Flask, request, redirect, session, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "SMARTTAILOR_SECRET"

DB = "tailor.db"
ADMIN_PASSWORD = "admin123"

# =========================
# DATABASE INIT
# =========================
def init_db():
    con = sqlite3.connect(DB)
    con.execute("""
    CREATE TABLE IF NOT EXISTS customers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        length TEXT,
        chest TEXT,
        waist TEXT,
        shoulder TEXT,
        sleeve TEXT,
        side_pocket TEXT,
        shalwar_pocket TEXT,
        cuff TEXT,
        collar TEXT,
        shalwar_length TEXT,
        zip TEXT,
        poncha TEXT,
        note TEXT,
        date TEXT
    )
    """)
    con.execute("""
    CREATE TABLE IF NOT EXISTS licenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tailor_name TEXT,
        key TEXT,
        active INTEGER
    )
    """)
    con.close()

init_db()

# =========================
# STYLE
# =========================
STYLE = """
<style>
body{font-family:Arial;background:#eef2f7}
.container{width:900px;margin:auto}
.card{background:white;padding:15px;margin:10px 0;border-radius:8px;box-shadow:0 0 10px #ccc}
h2{color:#0d6efd}
input,select{padding:6px;width:48%;margin:4px}
button{padding:8px 15px;background:#0d6efd;color:white;border:none;border-radius:4px}
a{color:red;text-decoration:none}
.top{display:flex;justify-content:space-between;align-items:center}
.back{margin-top:10px;display:inline-block}
</style>
"""

# =========================
# LICENSE CHECK DECORATOR
# =========================
def license_required(func):
    def wrapper(*args, **kwargs):
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM licenses WHERE active=1")
        active_count = cur.fetchone()[0]
        con.close()
        if active_count == 0:
            return render_template_string(STYLE + """
            <div class="container card">
            <h2>License Not Activated</h2>
            <p>Please contact admin.</p>
            </div>
            """)
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# =========================
# USER PANEL
# =========================
@app.route("/", methods=["GET","POST"])
@license_required
def user():
    if request.method == "POST":
        fields = [
            "name","phone","length","chest","waist","shoulder","sleeve",
            "side_pocket","shalwar_pocket","cuff","collar",
            "shalwar_length","zip","poncha","note"
        ]
        data = [request.form.get(f) for f in fields]
        data.append(datetime.now().strftime("%d-%m-%Y"))

        con = sqlite3.connect(DB)
        con.execute("""
        INSERT INTO customers VALUES(
        NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, data)
        con.commit()
        con.close()
        return redirect("/list")

    return render_template_string(STYLE + """
    <div class="container">
    <h2>User Panel - Add Measurement</h2>
    <form method="post" class="card">
    """ + "".join([f'<input name="{f}" placeholder="{f.replace("_"," ").title()}">' for f in [
        "name","phone","length","chest","waist","shoulder","sleeve",
        "side_pocket","shalwar_pocket","cuff","collar",
        "shalwar_length","zip","poncha","note"
    ]]) + """
    <br><button>Save Measurement</button>
    </form>
    <a class="back" href="/list">View Records</a>
    </div>
    """)

# =========================
# VIEW + SEARCH
# =========================
@app.route("/list")
@license_required
def list_data():
    q = request.args.get("q","")
    con = sqlite3.connect(DB)
    cur = con.cursor()

    if q:
        cur.execute("SELECT * FROM customers WHERE name LIKE ?",('%'+q+'%',))
    else:
        cur.execute("SELECT * FROM customers ORDER BY id DESC")

    rows = cur.fetchall()
    con.close()

    return render_template_string(STYLE + """
    <div class="container">
    <h2>Customer Records</h2>
    <form>
        <input name="q" placeholder="Search by name">
        <button>Search</button>
    </form>

    {% for r in rows %}
    <div class="card">
    <b>{{r[1]}}</b> | {{r[2]}} | {{r[16]}}<br>
    Length {{r[3]}} | Chest {{r[4]}} | Waist {{r[5]}}<br>
    Shoulder {{r[6]}} | Sleeve {{r[7]}}<br>
    Side Pocket {{r[8]}} | Shalwar Pocket {{r[9]}}<br>
    Cuff {{r[10]}} | Collar {{r[11]}}<br>
    Shalwar Length {{r[12]}} | Zip {{r[13]}} | Poncha {{r[14]}}<br>
    Note {{r[15]}}<br>
    </div>
    {% endfor %}
    <a class="back" href="/">Back to Add Measurement</a>
    </div>
    """, rows=rows)

# =========================
# ADMIN PANEL
# =========================
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True

    if not session.get("admin"):
        return render_template_string(STYLE + """
        <div class="container card">
        <h2>Admin Login</h2>
        <form method="post">
        <input type="password" name="password" placeholder="Password" required>
        <button>Login</button>
        </form>
        </div>
        """)

    con = sqlite3.connect(DB)
    rows = con.execute("SELECT * FROM licenses").fetchall()
    total_customers = con.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    con.close()

    return render_template_string(STYLE + """
    <div class="container">
    <h2>Admin Dashboard</h2>
    <p>Total Customers: {{total_customers}}</p>
    <h3>Licenses</h3>
    <form method="post" action="/add_license">
        <input name="tailor_name" placeholder="Tailor Name" required>
        <input name="key" placeholder="License Key" required>
        <select name="active">
            <option value="1">Active</option>
            <option value="0">Inactive</option>
        </select>
        <button>Add License</button>
    </form>
    {% for r in rows %}
    <div class="card">
        {{r[1]}} | {{r[2]}} | Status: {% if r[3]==1 %}Active{% else %}Inactive{% endif %}
        <a href="/delete_license/{{r[0]}}">❌ Remove</a>
        <a href="/toggle_license/{{r[0]}}">Toggle Status</a>
    </div>
    {% endfor %}
    <a class="back" href="/logout">Logout</a>
    </div>
    """, rows=rows,total_customers=total_customers)

@app.route("/add_license", methods=["POST"])
def add_license():
    if not session.get("admin"):
        return redirect("/admin")
    tailor_name = request.form.get("tailor_name")
    key = request.form.get("key")
    active = int(request.form.get("active",0))
    con = sqlite3.connect(DB)
    con.execute("INSERT INTO licenses VALUES(NULL,?,?,?)",(tailor_name,key,active))
    con.commit()
    con.close()
    return redirect("/admin")

@app.route("/delete_license/<id>")
def delete_license(id):
    if not session.get("admin"):
        return redirect("/admin")
    con = sqlite3.connect(DB)
    con.execute("DELETE FROM licenses WHERE id=?",(id,))
    con.commit()
    con.close()
    return redirect("/admin")

@app.route("/toggle_license/<id>")
def toggle_license(id):
    if not session.get("admin"):
        return redirect("/admin")
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("SELECT active FROM licenses WHERE id=?",(id,))
    status = cur.fetchone()[0]
    new_status = 0 if status==1 else 1
    con.execute("UPDATE licenses SET active=? WHERE id=?",(new_status,id))
    con.commit()
    con.close()
    return redirect("/admin")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/admin")

# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)