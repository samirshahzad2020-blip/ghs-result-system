import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Initialize data containers
if 'teachers' not in st.session_state:
    st.session_state['teachers'] = pd.DataFrame(columns=['TeacherID', 'Name'])
if 'students' not in st.session_state:
    st.session_state['students'] = pd.DataFrame(columns=['StudentID', 'Name'])
if 'marks' not in st.session_state:
    st.session_state['marks'] = pd.DataFrame(columns=['StudentID', 'Subject', 'Marks'])

st.title("School Result Card Generator App")

# Sidebar for navigation
menu = ["Teacher Management", "Student Management", "Marks Entry", "Results"]
choice = st.sidebar.selectbox("Navigate", menu)

# Teacher Management
if choice == "Teacher Management":
    st.header("Teacher Management")
    with st.form("add_teacher_form"):
        teacher_id = st.text_input("Teacher ID")
        name = st.text_input("Name")
        submitted = st.form_submit_button("Add Teacher")
        if submitted:
            st.session_state['teachers'] = st.session_state['teachers'].append(
                {'TeacherID': teacher_id, 'Name': name}, ignore_index=True)
            st.success("Teacher added!")

    st.subheader("All Teachers")
    st.dataframe(st.session_state['teachers'])

# Student Management
elif choice == "Student Management":
    st.header("Student Management")
    with st.form("add_student_form"):
        student_id = st.text_input("Student ID")
        name = st.text_input("Name")
        submitted = st.form_submit_button("Add Student")
        if submitted:
            st.session_state['students'] = st.session_state['students'].append(
                {'StudentID': student_id, 'Name': name}, ignore_index=True)
            st.success("Student added!")

    st.subheader("All Students")
    st.dataframe(st.session_state['students'])

# Marks Entry
elif choice == "Marks Entry":
    st.header("Marks Entry")
    if st.session_state['students'].empty:
        st.warning("Add students first.")
    else:
        student_id = st.selectbox("Select Student", st.session_state['students']['StudentID'])
        subject = st.text_input("Subject")
        marks = st.number_input("Marks", min_value=0, max_value=100)
        if st.button("Add Marks"):
            st.session_state['marks'] = st.session_state['marks'].append(
                {'StudentID': student_id, 'Subject': subject, 'Marks': marks}, ignore_index=True)
            st.success("Marks added!")

    st.subheader("All Marks")
    st.dataframe(st.session_state['marks'])

# Results and PDF Generation
elif choice == "Results":
    st.header("Generate Student Result Card")
    if st.session_state['students'].empty or st.session_state['marks'].empty:
        st.warning("Add students and marks first.")
    else:
        student_id = st.selectbox("Select Student", st.session_state['students']['StudentID'])
        student_name = st.session_state['students'].loc[
            st.session_state['students']['StudentID'] == student_id, 'Name'].values[0]
        student_marks = st.session_state['marks'][st.session_state['marks']['StudentID'] == student_id]

        # Calculate grades (simple example)
        def get_grade(marks):
            if marks >= 90:
                return 'A'
            elif marks >= 75:
                return 'B'
            elif marks >= 60:
                return 'C'
            else:
                return 'F'

        report_buffer = BytesIO()
        c = canvas.Canvas(report_buffer, pagesize=letter)
        c.setFont("Helvetica", 14)
        c.drawString(50, 750, f"Result Card for {student_name}")
        c.setFont("Helvetica", 12)
        y = 700
        total_marks = 0
        count = 0
        for index, row in student_marks.iterrows():
            grade = get_grade(row['Marks'])
            c.drawString(50, y, f"{row['Subject']}: {row['Marks']} (Grade: {grade})")
            y -= 30
            total_marks += row['Marks']
            count += 1
        average = total_marks / count if count else 0
        c.drawString(50, y - 20, f"Average Marks: {average:.2f}")
        c.save()

        report_buffer.seek(0)
        st.download_button("Download Result PDF", report_buffer, file_name=f"{student_name}_result.pdf")
