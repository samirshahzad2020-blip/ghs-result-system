# ==============================
# SCHOOL RESULT SYSTEM (ALL-IN-ONE)
# ==============================

import streamlit as st
import sqlite3
import hashlib
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="School Result System", layout="wide")
DB_NAME = "database.db"

# -----------------------------
# DATABASE
# -----------------------------
def connect():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = connect()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        father_name TEXT,
        roll TEXT UNIQUE,
        section TEXT,
        session TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS teachers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        assigned_class TEXT,
        subjects TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS marks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        subject TEXT,
        marks INTEGER,
        total INTEGER,
        teacher_id INTEGER,
        UNIQUE(student_id,subject))""")

    conn.commit()
    conn.close()

init_db()

# -----------------------------
# AUTH
# -----------------------------
def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def login(username, password):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id,role,password FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()

    if user and user[2] == hash_pass(password):
        return {"id": user[0], "role": user[1]}
    return None

# create default admin if not exists
conn = connect()
c = conn.cursor()
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute("INSERT INTO users(username,password,role) VALUES (?,?,?)",
              ("admin", hash_pass("admin123"), "admin"))
conn.commit()
conn.close()

# -----------------------------
# GRADING
# -----------------------------
def grade(p):
    if p >= 90: return "A+"
    elif p >= 80: return "A"
    elif p >= 70: return "B+"
    elif p >= 60: return "B"
    elif p >= 50: return "C"
    return "F"

# -----------------------------
# PDF GENERATOR
# -----------------------------
def generate_pdf(student, marks, position):

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(
        "<b>Govt High School Bhutta Mohabbat</b>", styles["Title"]))
    elements.append(Paragraph("EMIS Code: 39310025", styles["Normal"]))
    elements.append(Spacer(1, 20))

    info = f"""
    <b>Student:</b> {student['name']}<br/>
    <b>Father:</b> {student['father_name']}<br/>
    <b>Class:</b> {student['section']} &nbsp;&nbsp;
    <b>Roll:</b> {student['roll']}<br/>
    <b>Session:</b> {student['session']}
    """

    elements.append(Paragraph(info, styles["Normal"]))
    elements.append(Spacer(1, 20))

    data = [["Subject","Obtained","Total","Grade"]]

    total = 0
    max_total = 0

    for m in marks:
        perc = (m[1]/m[2])*100 if m[2] else 0
        g = grade(perc)
        data.append([m[0], m[1], m[2], g])
        total += m[1]
        max_total += m[2]

    percentage = (total/max_total*100) if max_total else 0
    final_grade = grade(percentage)

    data.append(["Grand Total", total, max_total, final_grade])
    data.append(["Percentage", f"{percentage:.2f}%", "", f"Position {position}"])

    table = Table(data, colWidths=[150,100,100,100])
    table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),1,colors.black),
        ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
        ("ALIGN",(1,1),(-1,-1),"CENTER"),
    ]))

    elements.append(table)
    elements.append(Spacer(1,30))
    elements.append(Paragraph("Senior Headmaster: Safdar Javed", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# -----------------------------
# SESSION
# -----------------------------
if "user" not in st.session_state:
    st.session_state.user = None

# -----------------------------
# LOGIN PAGE
# -----------------------------
if not st.session_state.user:

    st.title("School Result System Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login(u,p)
        if user:
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Invalid Login")

# -----------------------------
# MAIN APP
# -----------------------------
else:

    conn = connect()
    c = conn.cursor()

    role = st.session_state.user["role"]

    menu = st.sidebar.selectbox(
        "Menu",
        ["Admin","Teacher","Results"]
    )

    # ================= ADMIN =================
    if menu=="Admin" and role=="admin":

        st.header("Admin Panel")

        tab = st.radio("Action",["Add Student","Add Teacher"])

        if tab=="Add Student":
            name = st.text_input("Name")
            father = st.text_input("Father Name")
            roll = st.text_input("Roll")
            section = st.selectbox("Section",["A","B"])
            session = st.text_input("Session","2025-26")

            if st.button("Add Student"):
                c.execute("""INSERT INTO students
                (name,father_name,roll,section,session)
                VALUES (?,?,?,?,?)""",
                (name,father,roll,section,session))
                conn.commit()
                st.success("Student Added")

        if tab=="Add Teacher":
            name = st.text_input("Teacher Name")
            subjects = st.text_input("Subjects comma separated")
            cls = st.selectbox("Class",["A","B"])

            if st.button("Add Teacher"):
                c.execute("""INSERT INTO teachers
                (name,assigned_class,subjects)
                VALUES (?,?,?)""",
                (name,cls,subjects))
                conn.commit()
                st.success("Teacher Added")

    # ================= TEACHER =================
    elif menu=="Teacher":

        st.header("Teacher Portal")

        c.execute("SELECT * FROM teachers LIMIT 1")
        teacher = c.fetchone()

        if teacher:
            subjects = teacher[3].split(",")

            c.execute("SELECT * FROM students WHERE section=?", (teacher[2],))
            students = c.fetchall()

            for s in students:
                st.subheader(f"{s[1]} (Roll {s[3]})")

                inputs = {}
                for sub in subjects:
                    inputs[sub] = st.number_input(
                        sub,0,100,key=f"{s[0]}_{sub}")

                if st.button("Save", key=f"save{s[0]}"):
                    for sub,mark in inputs.items():
                        c.execute("""
                        INSERT OR REPLACE INTO marks
                        (student_id,subject,marks,total,teacher_id)
                        VALUES (?,?,?,?,?)
                        """,(s[0],sub,mark,100,
                             st.session_state.user["id"]))

                    conn.commit()
                    st.success("Saved")

    # ================= RESULTS =================
    elif menu=="Results":

        st.header("Result Generator")

        c.execute("SELECT id,name,section FROM students")
        students = c.fetchall()

        names = {s[1]:(s[0],s[2]) for s in students}

        selected = st.selectbox("Student", list(names.keys()))

        if selected:
            sid, section = names[selected]

            c.execute("SELECT * FROM students WHERE id=?", (sid,))
            student = c.fetchone()

            c.execute("SELECT subject,marks,total FROM marks WHERE student_id=?", (sid,))
            marks = c.fetchall()

            if marks:

                # merit
                c.execute("""
                SELECT s.id, SUM(m.marks)
                FROM students s
                JOIN marks m ON s.id=m.student_id
                WHERE s.section=?
                GROUP BY s.id
                ORDER BY SUM(m.marks) DESC
                """,(section,))
                ranking = c.fetchall()
                position = [r[0] for r in ranking].index(sid)+1

                total = sum(m[1] for m in marks)
                max_total = sum(m[2] for m in marks)
                percentage = total/max_total*100
                st.write(f"Total: {total}/{max_total}")
                st.write(f"Percentage: {percentage:.2f}%")
                st.write(f"Grade: {grade(percentage)}")
                st.write(f"Position: {position}")

                if st.button("Generate PDF"):
                    pdf = generate_pdf(
                        {
                            "name":student[1],
                            "father_name":student[2],
                            "roll":student[3],
                            "section":student[4],
                            "session":student[5]
                        },
                        marks,
                        position
                    )

                    st.download_button(
                        "Download Result",
                        pdf,
                        file_name=f"{student[1]}_result.pdf"
                    )

    if st.sidebar.button("Logout"):
        st.session_state.user=None
        st.rerun()

    conn.close()
