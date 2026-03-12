import streamlit as st
import pandas as pd
from fpdf import FPDF

# --- APP CONFIGURATION ---
st.set_page_config(page_title="School Manager", layout="wide", page_icon="🏫")

# Initialize session state for data persistence (in-memory)
if 'students' not in st.session_state:
    st.session_state.students = pd.DataFrame([
        {"ID": "S001", "Name": "Alice Johnson", "Class": "10A", "Math": 85, "Science": 90, "English": 78},
        {"ID": "S002", "Name": "Bob Smith", "Class": "10A", "Math": 72, "Science": 65, "English": 80}
    ])

if 'teachers' not in st.session_state:
    st.session_state.teachers = pd.DataFrame([
        {"ID": "T101", "Name": "Mr. Williams", "Subject": "Math"},
        {"ID": "T102", "Name": "Ms. Davis", "Subject": "Science"}
    ])

# --- LOGIC FUNCTIONS ---

def get_grade(score):
    if score >= 90: return "A+"
    elif score >= 80: return "A"
    elif score >= 70: return "B"
    elif score >= 60: return "C"
    elif score >= 50: return "D"
    else: return "F"

def generate_pdf(student):
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="STUDENT PROGRESS REPORT", ln=True, align='C')
    pdf.ln(10)
    
    # Info
    pdf.set_font("Arial", '', 12)
    pdf.cell(100, 10, txt=f"Name: {student['Name']}", ln=False)
    pdf.cell(100, 10, txt=f"ID: {student['ID']}", ln=True)
    pdf.cell(100, 10, txt=f"Class: {student['Class']}", ln=True)
    pdf.ln(10)
    
    # Grades Table
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(60, 10, "Subject", 1, 0, 'C', True)
    pdf.cell(60, 10, "Marks", 1, 0, 'C', True)
    pdf.cell(60, 10, "Grade", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 12)
    subjects = ["Math", "Science", "English"]
    total = 0
    for sub in subjects:
        score = student[sub]
        total += score
        pdf.cell(60, 10, sub, 1)
        pdf.cell(60, 10, str(score), 1, 0, 'C')
        pdf.cell(60, 10, get_grade(score), 1, 1, 'C')
    
    # Total
    avg = total / 3
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(120, 10, "Average Score:", 0)
    pdf.cell(60, 10, f"{avg:.2f}%", 0, 1)
    
    return pdf.output(dest='S').encode('latin-1')

# --- USER INTERFACE ---

def login():
    st.title("🏫 School Management Login")
    with st.container():
        role = st.selectbox("Select Role", ["Administrator", "Teacher"])
        key = st.text_input("Access Key", type="password")
        if st.button("Login"):
            if key == "admin123": # Simplified auth for demo
                st.session_state.logged_in = True
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Incorrect Access Key")

def admin_panel():
    st.header("🛡️ Admin Dashboard")
    tab1, tab2 = st.tabs(["Student Management", "Teacher Management"])
    
    with tab1:
        st.subheader("Register Students")
        with st.form("add_student"):
            c1, c2, c3 = st.columns(3)
            sid = c1.text_input("Student ID")
            sname = c2.text_input("Name")
            scls = c3.text_input("Class")
            if st.form_submit_button("Add Student"):
                new_s = {"ID": sid, "Name": sname, "Class": scls, "Math": 0, "Science": 0, "English": 0}
                st.session_state.students = pd.concat([st.session_state.students, pd.DataFrame([new_s])], ignore_index=True)
                st.success("Student Registered!")
        st.dataframe(st.session_state.students, use_container_width=True)

    with tab2:
        st.subheader("Manage Teachers")
        with st.form("add_teacher"):
            t1, t2, t3 = st.columns(3)
            tid = t1.text_input("Teacher ID")
            tname = t2.text_input("Name")
            tsub = t3.selectbox("Subject", ["Math", "Science", "English"])
            if st.form_submit_button("Add Teacher"):
                new_t = {"ID": tid, "Name": tname, "Subject": tsub}
                st.session_state.teachers = pd.concat([st.session_state.teachers, pd.DataFrame([new_t])], ignore_index=True)
                st.success("Teacher Hired!")
        st.dataframe(st.session_state.teachers, use_container_width=True)

def teacher_panel():
    st.header("📝 Teacher Grading Portal")
    sub_select = st.selectbox("Select Your Subject", ["Math", "Science", "English"])
    
    st.write(f"Editing marks for **{sub_select}**")
    
    # Use Data Editor for easy entry
    edited_df = st.data_editor(
        st.session_state.students[["ID", "Name", "Class", sub_select]],
        key="grade_editor",
        use_container_width=True,
        disabled=["ID", "Name", "Class"]
    )
    
    if st.button("Save Marks"):
        st.session_state.students.update(edited_df)
        st.success("Marks Saved Successfully!")

    st.divider()
    st.subheader("Generate Result Reports")
    target_student = st.selectbox("Select Student", st.session_state.students["Name"])
    if st.button("Generate PDF"):
        stu_data = st.session_state.students[st.session_state.students["Name"] == target_student].iloc[0]
        pdf_bytes = generate_pdf(stu_data)
        st.download_button(
            label=f"Download {target_student}'s Report",
            data=pdf_bytes,
            file_name=f"{target_student}_Report.pdf",
            mime="application/pdf"
        )

# --- MAIN APP FLOW ---
if 'logged_in' not in st.session_state:
    login()
else:
    st.sidebar.title("School App")
    st.sidebar.write(f"Current User: **{st.session_state.role}**")
    if st.sidebar.button("Logout"):
        del st.session_state.logged_in
        st.rerun()
    
    if st.session_state.role == "Administrator":
        admin_panel()
    else:
        teacher_panel()
