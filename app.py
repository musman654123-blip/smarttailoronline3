from flask import Flask, request, redirect, session, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "SMARTTAILOR_SECRET"

DB = "tailor.db"
ADMIN_PASSWORD = "admin123"

# =========================
# DATABASE
# =========================
def init_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS licenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tailor_name TEXT,
        license_key TEXT UNIQUE,
        active INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS customers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        license_key TEXT,
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

    con.commit()
    con.close()

init_db()

# =========================
# STYLE
# =========================
STYLE = """
<style>
body{font-family:Arial;background:#eef2f7}
.container{width:1000px;margin:auto;padding:20px}
.card{background:#fff;padding:15px;margin-bottom:15px;border-radius:8px;box-shadow:0 0 10px #ccc}
h2{color:#0d6efd}
input{padding:6px;width:48%;margin:4px}
button{padding:8px 15px;background:#0d6efd;color:white;border:none;border-radius:4px}
table{width:100%;border-collapse:collapse}
th,td{border:1px solid #ccc;padding:6px}
th{background:#0d6efd;color:white}
a{text-decoration:none;color:red}
.back{background:#6c757d}
</style>
"""

# =========================
# LICENSE CHECK
# =========================
def valid_license(key):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("SELECT active FROM licenses WHERE license_key=?", (key,))
    row = cur.fetchone()
    con.close()
    return row and row[0] == 1

# =========================
# LICENSE LOGIN (USER)
# =========================
@app.route("/", methods=["GET","POST"])
def license_login():
    if request.method == "POST":
        key = request.form["key"]
        if valid_license(key):
            session["license_key"] = key
            return redirect("/user")
        return "❌ Invalid or Deactivated License"

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
def user():
    if "license_key" not in session:
        return redirect("/")

    if request.method == "POST":
        f = request.form
        con = sqlite3.connect(DB)
        con.execute("""
        INSERT INTO customers VALUES
        (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            session["license_key"], f["name"], f["phone"],
            f["length"], f["chest"], f["waist"], f["shoulder"], f["sleeve"],
            f["side_pocket"], f["shalwar_pocket"], f["cuff"], f["collar"],
            f["shalwar_length"], f["zip"], f["poncha"],
            f["note"], datetime.now().strftime("%d-%m-%Y")
        ))
        con.commit()
        con.close()

    return render_template_string(STYLE + """
    <div class="container">
    <h2>User Measurement</h2>
    <a href="/view">View Records</a>
    <form method="post" class="card">
    """ + "".join([
        f'<input name="{x}" placeholder="{x.replace("_"," ").title()}">'
        for x in [
            "name","phone","length","chest","waist","shoulder","sleeve",
            "side_pocket","shalwar_pocket","cuff","collar",
            "shalwar_length","zip","poncha","note"
        ]
    ]) + """
    <br><button>Save</button>
    </form>
    </div>
    """)

# =========================
# VIEW RECORDS
# =========================
@app.route("/view")
def view():
    if "license_key" not in session:
        return redirect("/")

    q = request.args.get("q","")

    con = sqlite3.connect(DB)
    cur = con.cursor()

    if q:
        cur.execute("""
        SELECT * FROM customers
        WHERE license_key=?
        AND (name LIKE ? OR phone LIKE ?)
        ORDER BY id DESC
        """, (
            session["license_key"],
            "%"+q+"%",
            "%"+q+"%"
        ))
    else:
        cur.execute("""
        SELECT * FROM customers
        WHERE license_key=?
        ORDER BY id DESC
        """, (session["license_key"],))

    rows = cur.fetchall()
    con.close()

    return render_template_string(STYLE + """
    <div class="container">
    <h2>Customer Records</h2>

    <form method="get">
        <input name="q" placeholder="Search name or phone" value="{{request.args.get('q','')}}">
        <button>Search</button>
    </form>

    <table>
    <tr>
    <th>Name</th><th>Phone</th><th>Date</th>
    <th>Length</th><th>Chest</th><th>Waist</th>
    <th>Shoulder</th><th>Sleeve</th>
    <th>Side Pocket</th><th>Shalwar Pocket</th>
    <th>Cuff</th><th>Collar</th>
    <th>Shalwar Length</th><th>Zip</th>
    <th>Poncha</th><th>Note</th>
    </tr>

    {% for r in rows %}
    <tr>
    <td>{{r[2]}}</td>
    <td>{{r[3]}}</td>
    <td>{{r[18]}}</td>
    <td>{{r[4]}}</td>
    <td>{{r[5]}}</td>
    <td>{{r[6]}}</td>
    <td>{{r[7]}}</td>
    <td>{{r[8]}}</td>
    <td>{{r[9]}}</td>
    <td>{{r[10]}}</td>
    <td>{{r[11]}}</td>
    <td>{{r[12]}}</td>
    <td>{{r[13]}}</td>
    <td>{{r[14]}}</td>
    <td>{{r[15]}}</td>
    <td>{{r[16]}}</td>
    </tr>
    {% endfor %}
    </table>

    <br>
    <a href="/user"><button class="back">⬅ Back</button></a>
    </div>
    """, rows=rows)
# =========================
# ADMIN LOGIN
# =========================
@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True

    if not session.get("admin"):
        return render_template_string(STYLE + """
        <div class="container card">
        <h2>Admin Login</h2>
        <form method="post">
        <input type="password" name="password" placeholder="Admin Password">
        <button>Login</button>
        </form>
        </div>
        """)

    con = sqlite3.connect(DB)
    licenses = con.execute("SELECT * FROM licenses").fetchall()
    con.close()

    return render_template_string(STYLE + """
    <div class="container">
    <h2>Admin Dashboard</h2>

    <form method="post" action="/add-license" class="card">
        <input name="tailor" placeholder="Tailor Name" required>
        <input name="key" placeholder="License Key" required>
        <button>Add License</button>
    </form>

    <table>
    <tr><th>Tailor</th><th>License</th><th>Status</th><th>Action</th></tr>
    {% for l in licenses %}
    <tr>
        <td>{{l[1]}}</td>
        <td>{{l[2]}}</td>
        <td>{{"Active" if l[3] else "Inactive"}}</td>
        <td>
            <a href="/toggle/{{l[0]}}">Toggle</a> |
            <a href="/delete-license/{{l[0]}}">Delete</a>
        </td>
    </tr>
    {% endfor %}
    </table>
    </div>
    """, licenses=licenses)

@app.route("/add-license", methods=["POST"])
def add_license():
    if not session.get("admin"):
        return redirect("/admin")
    con = sqlite3.connect(DB)
    con.execute(
        "INSERT INTO licenses(tailor_name,license_key,active) VALUES(?,?,1)",
        (request.form["tailor"], request.form["key"])
    )
    con.commit()
    con.close()
    return redirect("/admin")

@app.route("/toggle/<id>")
def toggle(id):
    if not session.get("admin"):
        return redirect("/admin")
    con = sqlite3.connect(DB)
    con.execute("UPDATE licenses SET active = NOT active WHERE id=?", (id,))
    con.commit()
    con.close()
    return redirect("/admin")

@app.route("/delete-license/<id>")
def delete_license(id):
    if not session.get("admin"):
        return redirect("/admin")
    con = sqlite3.connect(DB)
    con.execute("DELETE FROM licenses WHERE id=?", (id,))
    con.commit()
    con.close()
    return redirect("/admin")

# =========================
if __name__ == "__main__":
    app.run(debug=True)