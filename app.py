from flask import Flask, request, redirect, session, render_template_string, url_for
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
        license_key TEXT,
        active INTEGER DEFAULT 0
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
input{padding:6px;width:48%;margin:4px}
button{padding:8px 15px;background:#0d6efd;color:white;border:none;border-radius:4px;cursor:pointer}
a{color:red;text-decoration:none;margin-left:10px}
.top{display:flex;justify-content:space-between;align-items:center}
.back{margin-top:10px;display:inline-block}
</style>
"""

# =========================
# LICENSE CHECK DECORATOR
# =========================
def license_required(f):
    def wrap(*args, **kwargs):
        if not session.get("license_active"):
            return redirect("/license")
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# =========================
# LICENSE PAGE
# =========================
@app.route("/license", methods=["GET", "POST"])
def license_page():
    if request.method == "POST":
        key = request.form.get("key")
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute("SELECT * FROM licenses WHERE license_key=? AND active=1", (key,))
        row = cur.fetchone()
        con.close()
        if row:
            session["license_active"] = True
            session["tailor_name"] = row[1]
            return redirect("/user")
        else:
            return render_template_string(STYLE + """
            <div class="container card">
            <h2>License Activation</h2>
            <p style="color:red">Invalid License Key</p>
            <form method="post">
            <input name="key" placeholder="Enter License Key" required>
            <button>Activate</button>
            </form>
            </div>
            """)
    return render_template_string(STYLE + """
    <div class="container card">
    <h2>License Activation</h2>
    <form method="post">
    <input name="key" placeholder="Enter License Key" required>
    <button>Activate</button>
    </form>
    </div>
    """)

# =========================
# USER PANEL
# =========================
@app.route("/user", methods=["GET","POST"])
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
        return redirect("/view")

    return render_template_string(STYLE + """
    <div class="container">
    <div class="top">
        <h2>User Panel</h2>
        <a href="/view">View Records</a>
    </div>
    <form method="post" class="card">
    """ + "".join([f'<input name="{f}" placeholder="{f.replace("_"," ").title()}">' for f in [
        "name","phone","length","chest","waist","shoulder","sleeve",
        "side_pocket","shalwar_pocket","cuff","collar",
        "shalwar_length","zip","poncha","note"]]) + """
    <br><button>Save Measurement</button>
    </form>
    </div>
    """)

# =========================
# VIEW + SEARCH
# =========================
@app.route("/view")
@license_required
def view_records():
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
    Note {{r[15]}}
    </div>
    {% endfor %}
    <a class="back" href="/user">Back</a>
    </div>
    """, rows=rows)

# =========================
# ADMIN PANEL
# =========================
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST" and not session.get("admin"):
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True

    if not session.get("admin"):
        return render_template_string(STYLE + """
        <div class="container card">
        <h2>Admin Login</h2>
        <form method="post">
        <input type="password" name="password">
        <button>Login</button>
        </form>
        </div>
        """)

    # Admin actions: add/remove license
    action = request.args.get("action")
    key = request.args.get("key")
    tailor_name = request.args.get("tailor")
    con = sqlite3.connect(DB)
    cur = con.cursor()
    if action=="add" and key and tailor_name:
        cur.execute("INSERT INTO licenses (tailor_name,license_key,active) VALUES (?,?,1)", (tailor_name,key))
        con.commit()
    if action=="remove" and key:
        cur.execute("DELETE FROM licenses WHERE license_key=?", (key,))
        con.commit()
    if action=="toggle" and key:
        cur.execute("SELECT active FROM licenses WHERE license_key=?", (key,))
        row = cur.fetchone()
        if row:
            new_status = 0 if row[0]==1 else 1
            cur.execute("UPDATE licenses SET active=? WHERE license_key=?", (new_status,key))
            con.commit()
    licenses = cur.execute("SELECT * FROM licenses").fetchall()
    total_customers = cur.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    con.close()

    return render_template_string(STYLE + """
    <div class="container">
    <h2>Admin Dashboard</h2>
    <p>Total Customers: {{total_customers}}</p>
    <table border="1" cellpadding="5" cellspacing="0">
    <tr><th>Tailor</th><th>License Key</th><th>Active</th><th>Actions</th></tr>
    {% for l in licenses %}
    <tr>
        <td>{{l[1]}}</td>
        <td>{{l[2]}}</td>
        <td>{{'✅' if l[3]==1 else '❌'}}</td>
        <td>
        <a href="/admin?action=toggle&key={{l[2]}}">Toggle</a> |
        <a href="/admin?action=remove&key={{l[2]}}">Remove</a>
        </td>
    </tr>
    {% endfor %}
    </table>
    <br>
    <h3>Add New License</h3>
    <form method="get">
    Tailor Name: <input name="tailor" required>
    License Key: <input name="key" required>
    <button>Add License</button>
    </form>
    <br><a href="/logout">Logout</a>
    </div>
    """, licenses=licenses, total_customers=total_customers)

# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/license")

# =========================
if __name__ == "__main__":
    app.run(debug=True)