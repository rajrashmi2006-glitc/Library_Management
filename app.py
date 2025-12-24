print("FLASK FILE STARTED")
from flask import Flask, render_template, request, redirect, flash, url_for
import mysql.connector
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "library_secret_key"

# ---------------- EMAIL CONFIG ----------------
EMAIL_ADDRESS = "rashmiraj0694@gmail.com"      # 🔴 your Gmail
EMAIL_PASSWORD = "cqod hueg rrqd tukr"       # 🔴 Gmail App Password

# ---------------- DATABASE CONNECTION ----------------
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Mysql@123",
        database="library_db"
    )

# ---------------- SEND EMAIL FUNCTION ----------------
def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("✅ Email sent to:", to_email)

    except Exception as e:
        print("❌ Email failed:", e)

# ---------------- HOME ----------------
@app.route("/")
def index():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM students")
    students = cur.fetchall()

    cur.execute("SELECT * FROM issued_books ORDER BY issue_date DESC")
    issued_books = cur.fetchall()

    cur.close()
    db.close()

    return render_template("index.html", students=students, issued_books=issued_books)


# ---------------- BOOK SEARCH ----------------
@app.route("/search", methods=["POST"])
def search():
    book_name = request.form.get("book")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Search book
    cur.execute("SELECT * FROM books WHERE book_name=%s", (book_name,))
    book = cur.fetchone()

    # Fetch students
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()

    # Fetch issued books
    cur.execute("SELECT * FROM issued_books ORDER BY issue_date DESC")
    issued_books = cur.fetchall()

    cur.close()
    db.close()

    if book:
        if book["quantity"] > 0:
            result = "Available"
            rack = book["rack"]
            row = book["row_no"]
        else:
            result = "Not Available"
            rack = None
            row = None
    else:
        result = "Book Not Found"
        rack = None
        row = None

    return render_template(
        "index.html",
        result=result,
        rack=rack,
        row=row,
        students=students,
        issued_books=issued_books
    )
                

# ---------------- STUDENT REGISTER ----------------
@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    usn = request.form["usn"]
    branch = request.form["branch"]
    semester = request.form["semester"]
    phone = request.form["phone"]
    email = request.form["email"]

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO students (usn, name, branch, semester, phone, email)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (usn, name, branch, semester, phone, email))

    db.commit()
    cur.close()
    db.close()

    # 📧 Registration Email
    body = f"""
Hello {name},

You are successfully registered in the Library Management System.

USN: {usn}
Branch: {branch}
Semester: {semester}

Library Admin
"""
    send_email(email, "Library Registration Successful", body)

    flash("✅ Student registered and email sent")
    return redirect("/")


# ---------------- ISSUE BOOK ----------------
@app.route("/issue", methods=["POST"])
def issue_book():
    book_id = request.form["book_id"]
    book_name = request.form["book_name"]
    publisher = request.form["publisher"]
    student_usn = request.form["student_usn"]     # ✅ SAME AS HTML
    student_email = request.form["student_email"] # ✅ SAME AS HTML
    issue_date = request.form["issue_date"]
    return_date = request.form["return_date"]

    db = get_db()
    cur = db.cursor(buffered=True)

    # Check book availability
    cur.execute("SELECT quantity FROM books WHERE book_id=%s", (book_id,))
    q = cur.fetchone()
    if not q or q[0] <= 0:
        flash("❌ Book not available")
        return redirect("/")

    # Insert issue record
    cur.execute("""
        INSERT INTO issued_books
        (student_usn, student_email, book_id, book_name, publisher, issue_date, return_date, returned)
        VALUES (%s,%s,%s,%s,%s,%s,%s,0)
    """, (
        student_usn,
        student_email,
        book_id,
        book_name,
        publisher,
        issue_date,
        return_date
    ))

    # Update quantity
    cur.execute(
        "UPDATE books SET quantity = quantity - 1 WHERE book_id=%s",
        (book_id,)
    )

    db.commit()
    cur.close()
    db.close()

    # Send email to STUDENT (not admin)
    body = f"""
Hello Student,

Book Issued Successfully.

Student USN: {student_usn}
Book ID: {book_id}
Book Name: {book_name}
Publisher: {publisher}
Issue Date: {issue_date}
Return Date: {return_date}

Library Admin
"""
    send_email(student_email, "Book Issued Successfully", body)

    flash("✅ Book issued & email sent to student")
    return redirect(url_for("index"))


# ---------------- Add BOOK ----------------
@app.route("/add_book", methods=["POST"])
def add_book():
    book_id = request.form["book_id"]
    book_name = request.form["book_name"]
    publisher = request.form["publisher"]

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT quantity FROM books WHERE book_id=%s", (book_id,))
    book = cur.fetchone()

    if book:
        cur.execute("""
            UPDATE books
            SET quantity = quantity + 1
            WHERE book_id=%s
        """, (book_id,))
        msg = "✅ Book  updated successfully"
    else:
        cur.execute("""
            INSERT INTO books (book_id, book_name, publisher, quantity)
            VALUES (%s,%s,%s,1)
        """, (book_id, book_name, publisher))
        msg = "✅ Book added successfully"

    db.commit()
    cur.close()
    db.close()

    return render_template(
        "index.html",
        add_msg=msg
    )

# ---------------- RETURN BOOK ----------------
@app.route("/return", methods=["POST"])
def return_book():
    book_id = request.form["book_id"]
    book_name = request.form["book_name"]
    student_usn = request.form["student_usn"]

    db = get_db()
    cur = db.cursor(buffered=True)

    cur.execute("""
        SELECT issue_id FROM issued_books
        WHERE book_id=%s AND book_name=%s AND student_usn=%s AND returned=0
    """, (book_id, book_name, student_usn))

    record = cur.fetchone()
    if not record:
        flash("❌ Book not issued or already returned")
        return redirect("/")

    cur.execute("UPDATE issued_books SET returned=1 WHERE issue_id=%s", (record[0],))
    cur.execute("UPDATE books SET quantity = quantity + 1 WHERE book_id=%s", (book_id,))
    db.commit()

    cur.close()
    db.close()
    flash("✅ Book returned")
    return redirect("/")

# ---------------- DAILY REMINDER & FINE ----------------
@app.route("/send_reminders")
def send_reminders():
    db = get_db()
    cur = db.cursor(dictionary=True)

    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)

    cur.execute("""
        SELECT ib.*, s.name, s.email
        FROM issued_books ib
        JOIN students s ON ib.student_usn = s.usn
        WHERE ib.returned=0
    """)
    records = cur.fetchall()

    for r in records:
        rd = r["return_date"]

        # Reminder
        if rd == tomorrow:
            body = f"""
Hello {r['name']},

Reminder: Book return date is tomorrow.

Book ID: {r['book_id']}
Book Name: {r['book_name']}

Library Admin
"""
            send_email(r["email"], "Book Return Reminder", body)

        # Fine
        if rd < today:
            days = (today - rd).days
            fine = days * 100
            body = f"""
Hello {r['name']},

Book overdue!

Book ID: {r['book_id']}
Days Late: {days}
Fine: ₹{fine}

Please return immediately.

Library Admin
"""
            send_email(r["email"], "Library Fine Notice", body)

    cur.close()
    db.close()
    return "Reminder emails sent"

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)