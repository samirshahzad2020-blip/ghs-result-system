# app.py

import streamlit as st
import pandas as pd
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

st.set_page_config(page_title="Student Result Generator", layout="wide")

# -------------------------------
# Paths for persistent storage
# -------------------------------
DATA_DIR = "data"
STUDENT_FILE = os.path.join(DATA_DIR, "students.csv")
MARKS_FILE = os.path.join(DATA_DIR, "marks.csv")
TEACHERS_FILE = os.path.join(DATA_DIR, "teachers.csv")
LOGO_PATH = "logo.png"

# -------------------------------
# Ensure data directory exists
# -------------------------------
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------
# Initialize CSVs if missing
# -------------------------------
def init_csv(file_path, columns):
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=columns)
        df.to_csv(file_path, index=False)
        return df
    else:
        return pd.read_csv(file_path)

students_df = init_csv(STUDENT_FILE, ["student_id","name","father_name","roll","section","session"])
marks_df = init_csv(MARKS_FILE, ["student_id","subject","marks_obtained","total_marks","teacher"])
teachers_df = init_csv(TEACHERS_FILE, ["teacher_name","assigned_subjects","assigned_class"])

# -------------------------------
# Helper functions
# -------------------------------
def calculate_grade(percentage):
    if percentage >= 90: return "A+"
    elif percentage >= 80: return "A"
    elif percentage >= 70: return "B+"
    elif percentage >= 60: return "B"
    elif percentage >= 50: return "C"
    else: return "F"

def generate_result_pdf(student_info, student_marks, teachers, logo_path=LOGO_PATH):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Logo
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 50, height-100, width=80, height=80, preserveAspectRatio=True)

    # School Info
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height-50, "Govt High School Bhutta Mohabbat")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height-70, "EMIS Code: 39310025")

    # Student Info
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height-150, f"Student Name: {student_info['name']}")
    c.drawString(50, height-170, f"Father Name: {student_info['father_name']}")
    c.drawString(50, height-190, f"Session: {student_info['session']}")
    c.drawString(50, height-210, f"Class: {student_info['section']}  Roll: {student_info['roll']}")

    # Marks Table
    c.drawString(50, height-240, "Subject-wise Marks:")
    y = height-260
    c.setFont("Helvetica", 11)
    c.drawString(50, y, "Subject")
    c.drawString(200, y, "Obtained Marks")
    c.drawString(350, y, "Total Marks")
    y -= 20
    for _, row in student_marks.iterrows():
        c.drawString(50, y, str(row['subject']))
        c.drawString(200, y, str(row['marks_obtained']))
        c.drawString(350, y, str(row['total_marks']))
        y -= 20

    # Grand Total
    grand_total = student_marks['marks_obtained'].sum()
    max_total = student_marks['total_marks'].sum()
    percentage = (grand_total/max_total)*100
    grade = calculate_grade(percentage)

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Grand Total: {grand_total}/{max_total}")
    y -= 20
    c.drawString(50, y, f"Percentage: {percentage:.2f}%")
    y -= 20
    c.drawString(50, y, f"Grade: {grade}")

    # Teachers and Headmaster
    y -= 40
    c.drawString(50, y, "Teacher(s): " + ", ".join(teachers))
    c.drawString(350, y, "Senior Headmaster: Safdar Javed")

    # Quotes
    y -= 40
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, y, "Education is the most powerful weapon which you can use to change the world.")
    y -= 15
    c.drawString(50, y, "The function of education is to teach one to think intensively and to think critically.")
    y -= 20
    c.drawString(50, y, "District: Okara")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# -------------------------------
# Header
# -------------------------------
col1, col2, col3 = st.columns([1,4,1])
with col1:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=80)
with col2:
    st.markdown("<h2 style='text-align:center;'>Govt High School Bhutta Mohabbat</h2>", unsafe_allow_html=True)
    st.markdown("<h5 style='text-align:center;'>EMIS Code: 39310025</h5>", unsafe_allow_html=True)
with col3:
    st.write("")

st.markdown("---")

# -------------------------------
# Sidebar Navigation
# -------------------------------
page = st.sidebar.selectbox("Select Page", ["Admin", "Teacher Portal", "Result Generator"])

# -------------------------------
# Admin
# -------------------------------
if page=="Admin":
    st.header("Admin Panel")
    tab = st.radio("Choose Action", ["Add Teacher","Add Student","View/Edit Data"])

    if tab=="Add Teacher":
        t_name = st.text_input("Teacher Name")
        t_class = st.selectbox("Assigned Class", ["A","B"])
        t_subjects = st.multiselect("Assigned Subjects", ["Urdu","English","Islamiat","Tarjuma-tul-Quran","Maths","Science","Social Studies","Nazra Quran","GK"])
        if st.button("Add Teacher"):
            if t_name and t_class and t_subjects:
                if t_name in teachers_df['teacher_name'].values:
                    st.warning("Teacher already exists!")
                else:
                    teachers_df = pd.concat([teachers_df,pd.DataFrame([{"teacher_name":t_name,"assigned_subjects":",".join(t_subjects),"assigned_class":t_class}])],ignore_index=True)
                    teachers_df.to_csv(TEACHERS_FILE,index=False)
                    st.success(f"Teacher {t_name} added!")

    elif tab=="Add Student":
        s_name = st.text_input("Student Name")
        f_name = st.text_input("Father Name")
        roll = st.text_input("Roll Number")
        s_class = st.selectbox("Class Section", ["A","B"])
        session = st.text_input("Session", value="2025-2026")
        if st.button("Add Student"):
            if s_name and f_name and roll and s_class and session:
                if roll in students_df['roll'].values:
                    st.warning("Roll exists!")
                else:
                    new_id = students_df['student_id'].max()+1 if not students_df.empty else 1
                    students_df = pd.concat([students_df,pd.DataFrame([{"student_id":new_id,"name":s_name,"father_name":f_name,"roll":roll,"section":s_class,"session":session}])],ignore_index=True)
                    students_df.to_csv(STUDENT_FILE,index=False)
                    st.success(f"Student {s_name} added!")

    elif tab=="View/Edit Data":
        st.subheader("Teachers")
        st.dataframe(teachers_df)
        st.subheader("Students")
        st.dataframe(students_df)
        st.subheader("Marks")
        st.dataframe(marks_df)

# -------------------------------
# Teacher Portal
# -------------------------------
elif page=="Teacher Portal":
    st.header("Teacher Portal")
    teacher_name = st.text_input("Enter Teacher Name")
    if teacher_name and teacher_name in teachers_df['teacher_name'].values:
        t_info = teachers_df[teachers_df['teacher_name']==teacher_name].iloc[0]
        assigned_subjects = t_info['assigned_subjects'].split(",")
        assigned_class = t_info['assigned_class']

        st.success(f"Welcome {teacher_name}! Class {assigned_class}, subjects: {', '.join(assigned_subjects)}")
        class_students = students_df[students_df['section']==assigned_class]

        for _, student in class_students.iterrows():
            st.markdown(f"### {student['name']} (Roll: {student['roll']})")
            cols = st.columns(len(assigned_subjects))
            marks_input = {}
            for i, subject in enumerate(assigned_subjects):
                existing = marks_df[(marks_df['student_id']==student['student_id']) & (marks_df['subject']==subject)]
                current = int(existing['marks_obtained'].values[0]) if not existing.empty else 0
                marks_input[subject] = cols[i].number_input(subject, min_value=0, max_value=100, value=current, key=f"{student['student_id']}_{subject}")
            if st.button(f"Save Marks {student['name']}", key=f"save_{student['student_id']}"):
                for subject, mark in marks_input.items():
                    idx = marks_df[(marks_df['student_id']==student['student_id']) & (marks_df['subject']==subject)].index
                    if len(idx)>0:
                        marks_df.at[idx[0],'marks_obtained']=mark
                        marks_df.at[idx[0],'total_marks']=100
                        marks_df.at[idx[0],'teacher']=teacher_name
                    else:
                        marks_df = pd.concat([marks_df,pd.DataFrame([{"student_id":student['student_id'],"subject":subject,"marks_obtained":mark,"total_marks":100,"teacher":teacher_name}])],ignore_index=True)
                marks_df.to_csv(MARKS_FILE,index=False)
                st.success(f"Marks saved for {student['name']}!")

    elif teacher_name:
        st.warning("Teacher not found! Ask admin to add.")

# -------------------------------
# Result Generator
# -------------------------------
elif page=="Result Generator":
    st.header("Generate Student Result")
    section = st.selectbox("Class Section", ["A","B"])
    students_in_class = students_df[students_df['section']==section]
    if not students_in_class.empty:
        selected = st.selectbox("Select Student", students_in_class['name'])
        student_info = students_in_class[students_in_class['name']==selected].iloc[0]
        student_marks = marks_df[marks_df['student_id']==student_info['student_id']]
        if not student_marks.empty:
            grand_total = student_marks['marks_obtained'].sum()
            max_total = student_marks['total_marks'].sum()
            percentage = (grand_total/max_total)*100
            grade = calculate_grade(percentage)

            col1,col2 = st.columns(2)
            with col1:
                st.write("Teacher(s):", ", ".join(student_marks['teacher'].unique()))
            with col2:
                st.write("Senior Headmaster: Safdar Javed")

            st.markdown(f"**Student Name:** {student_info['name']}")
            st.markdown(f"**Father Name:** {student_info['father_name']}")
            st.markdown(f"**Session:** {student_info['session']} | Class: {student_info['section']} | Roll: {student_info['roll']}")
            st.table(student_marks[['subject','marks_obtained','total_marks']])
            st.markdown(f"**Grand Total:** {grand_total}/{max_total}")
            st.markdown(f"**Percentage:** {percentage:.2f}%")
            st.markdown(f"**Grade:** {grade}")

            st.markdown("---")
            st.markdown("> Education is the most powerful weapon which you can use to change the world.")
            st.markdown("> The function of education is to teach one to think intensively and to think critically.")
            st.markdown("**District: Okara**")

            if st.button("Download PDF Result"):
                pdf_buffer = generate_result_pdf(student_info, student_marks, list(student_marks['teacher'].unique()))
                st.download_button("Download PDF", data=pdf_buffer, file_name=f"{student_info['name']}_result.pdf", mime="application/pdf")
        else:
            st.info("No marks entered yet.")
