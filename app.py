from flask import Flask, request, redirect, session, render_template_string, abort
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "SMARTTAILOR_SECRET"

DB = "tailor.db"
ADMIN_PASSWORD = "admin123"

# =========================
# DATABASE INIT
# =========================
def db():
    return sqlite3.connect(DB)

def init_db():
    con = db()
    cur = con.cursor()

    # License table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS license(
        id INTEGER PRIMARY KEY,
        active INTEGER
    )
    """)

    # Customers table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS customers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, phone TEXT,
        length TEXT, chest TEXT, waist TEXT,
        shoulder TEXT, sleeve TEXT,
        side_pocket TEXT, shalwar_pocket TEXT,
        cuff TEXT, collar TEXT,
        shalwar_length TEXT, zip TEXT, poncha TEXT,
        note TEXT, date TEXT
    )
    """)

    # Default license row
    cur.execute("SELECT * FROM license")
    if not cur.fetchone():
        cur.execute("INSERT INTO license VALUES (1, 0)")

    con.commit()
    con.close()

init_db()

# =========================
# STYLE
# =========================
STYLE = """
<style>
body{font-family:Arial;background:#eef2f7}
.container{width:1000px;margin:auto}
.card{background:white;padding:15px;margin:10px 0;border-radius:8px;box-shadow:0 0 10px #ccc}
h2{color:#0d6efd}
input,textarea{padding:6px;width:48%;margin:4px}
button{padding:8px 15px;background:#0d6efd;color:white;border:none;border-radius:4px}
a{text-decoration:none;margin-right:10px}
.top{display:flex;justify-content:space-between}
table{width:100%;border-collapse:collapse}
td,th{border:1px solid #ccc;padding:6px;text-align:left}
</style>
"""

# =========================
# LICENSE CHECK
# =========================
def license_active():
    con = db()
    cur = con.cursor()
    cur.execute("SELECT active FROM license WHERE id=1")
    status = cur.fetchone()[0]
    con.close()
    return status == 1

# =========================
# HOME
# =========================
@app.route("/")
def home():
    if not license_active():
        return render_template_string(STYLE + """
        <div class="container card">
        <h2>License Not Activated</h2>
        <p>Please contact admin.</p>
        <a href="/admin">Admin Login</a>
        </div>
        """)
    return redirect("/user")

# =========================
# USER PANEL
# =========================
@app.route("/user", methods=["GET","POST"])
def user():
    if not license_active():
        return redirect("/")

    if request.method == "POST":
        fields = [
            "name","phone","length","chest","waist","shoulder","sleeve",
            "side_pocket","shalwar_pocket","cuff","collar",
            "shalwar_length","zip","poncha","note"
        ]
        data = [request.form.get(f) for f in fields]
        data.append(datetime.now().strftime("%d-%m-%Y"))

        con = db()
        con.execute("""
        INSERT INTO customers VALUES
        (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, data)
        con.commit()
        con.close()

    return render_template_string(STYLE + """
    <div class="container">
    <div class="top">
        <h2>User Panel</h2>
        <div>
            <a href="/view">View</a>
            <a href="/logout">Logout</a>
        </div>
    </div>

    <form method="post" class="card">
    """ + "".join([
        f'<input name="{f}" placeholder="{f.replace("_"," ").title()}">'
        for f in [
            "name","phone","length","chest","waist","shoulder","sleeve",
            "side_pocket","shalwar_pocket","cuff","collar",
            "shalwar_length","zip","poncha"
        ]
    ]) + """
    <textarea name="note" placeholder="Note" style="width:98%"></textarea><br>
    <button>Save</button>
    </form>
    </div>
    """)

# =========================
# VIEW + SEARCH
# =========================
@app.route("/view")
def view():
    if not license_active():
        return redirect("/")

    q = request.args.get("q","")
    con = db()
    cur = con.cursor()
    if q:
        cur.execute("SELECT * FROM customers WHERE name LIKE ? OR phone LIKE ?",('%'+q+'%','%'+q+'%'))
    else:
        cur.execute("SELECT * FROM customers ORDER BY id DESC")
    rows = cur.fetchall()
    con.close()

    return render_template_string(STYLE + """
    <div class="container">
    <h2>Customer Records</h2>
    <form>
        <input name="q" placeholder="Search name or phone">
        <button>Search</button>
        <a href="/user">Back</a>
    </form>

    <table>
    <tr>
        <th>Name</th><th>Phone</th><th>Date</th><th>Action</th>
    </tr>
    {% for r in rows %}
    <tr>
        <td>{{r[1]}}</td>
        <td>{{r[2]}}</td>
        <td>{{r[16]}}</td>
        <td><a href="/print/{{r[0]}}">Print</a></td>
    </tr>
    {% endfor %}
    </table>
    </div>
    """, rows=rows)

# =========================
# PRINT
# =========================
@app.route("/print/<int:id>")
def print_view(id):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM customers WHERE id=?", (id,))
    r = cur.fetchone()
    con.close()
    if not r:
        abort(404)

    return render_template_string(STYLE + """
    <div class="container card">
    <h2>{{r[1]}}</h2>
    <p>Phone: {{r[2]}}</p>
    <p>Length {{r[3]}}, Chest {{r[4]}}, Waist {{r[5]}}</p>
    <p>Shoulder {{r[6]}}, Sleeve {{r[7]}}</p>
    <p>Side Pocket {{r[8]}}, Shalwar Pocket {{r[9]}}</p>
    <p>Cuff {{r[10]}}, Collar {{r[11]}}</p>
    <p>Shalwar Length {{r[12]}}, Zip {{r[13]}}, Poncha {{r[14]}}</p>
    <p>Note {{r[15]}}</p>
    <button onclick="window.print()">Print</button>
    <a href="/view">Back</a>
    </div>
    """, r=r)

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
        <input type="password" name="password">
        <button>Login</button>
        </form>
        </div>
        """)

    con = db()
    cur = con.cursor()
    cur.execute("SELECT active FROM license WHERE id=1")
    active = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM customers")
    total = cur.fetchone()[0]
    con.close()

    return render_template_string(STYLE + """
    <div class="container">
    <h2>Admin Dashboard</h2>
    <p>License Status: <b>{{'Active' if active else 'Inactive'}}</b></p>
    <p>Total Customers: {{total}}</p>

    <a href="/toggle">Toggle License</a>
    <a href="/logout">Logout</a>
    </div>
    """, active=active, total=total)

@app.route("/toggle")
def toggle():
    if not session.get("admin"):
        return redirect("/admin")
    con = db()
    cur = con.cursor()
    cur.execute("UPDATE license SET active = NOT active WHERE id=1")
    con.commit()
    con.close()
    return redirect("/admin")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)