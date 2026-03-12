import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- APP CONFIG ---
st.set_page_config(page_title="GHS Bhutta Mohabbat Portal", layout="wide", page_icon="🏫")

# --- INITIALIZE DATA ---
# We use all subjects from your provided sample image
SUBJECTS = [
    "English", "Urdu", "Mathematics", "Islamiat", 
    "Science", "Social Study", "Computer", "Tajuma-tu-Quran"
]

if 'students_db' not in st.session_state:
    st.session_state.students_db = pd.DataFrame([
        {
            "Roll No": 12, "Name": "FAIZ", "Father Name": "SARWAR", 
            "Class": "9", "Section": "A",
            **{sub: 40 for sub in SUBJECTS} # Default marks
        }
    ])

# --- CALCULATION LOGIC ---
def get_grade(percentage):
    if percentage >= 80: return "A+"
    elif percentage >= 70: return "A"
    elif percentage >= 60: return "B"
    elif percentage >= 50: return "C"
    elif percentage >= 40: return "D"
    else: return "F"

def get_performance(grade):
    perf = {"A+": "Excellent", "A": "Very Good", "B": "Good", "C": "Satisfactory", "D": "Fair", "F": "Poor"}
    return perf.get(grade, "---")

# --- PDF GENERATOR (EXACT SAMPLE MATCH) ---
class ResultPDF(FPDF):
    def draw_report_card(self, data):
        self.add_page()
        # Outer Border
        self.rect(5, 5, 200, 287)
        self.rect(7, 7, 196, 283)
        
        # Header Area
        self.set_font("Arial", 'B', 8)
        self.cell(190, 5, "SCHOOL EDUCATION DEPARTMENT", ln=True, align='C')
        self.set_font("Arial", 'B', 14)
        self.cell(190, 7, "GOVT. HIGH SCHOOL BHUTTA MOHABBAT", ln=True, align='C')
        self.set_font("Arial", 'B', 9)
        self.cell(190, 5, "EMIS CODE: 39310025 | DISTRICT OKARA", ln=True, align='C')
        self.ln(2)
        
        self.set_font("Arial", 'B', 16)
        self.set_text_color(100, 149, 237) # Cornflower Blue
        self.cell(190, 10, "STUDENT REPORT CARD", ln=True, align='C')
        self.set_text_color(0, 0, 0)
        
        self.set_font("Arial", 'B', 10)
        self.cell(190, 8, "Session 2025-2026", ln=True)
        
        # Student Info Table
        self.set_fill_color(123, 153, 180)
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", 'B', 9)
        self.cell(95, 7, f" NAME: {str(data['Name']).upper()}", 1, 0, 'L', True)
        self.cell(95, 7, f" FATHER NAME: {str(data['Father Name']).upper()}", 1, 1, 'L', True)
        self.cell(63, 7, f" CLASS: {data['Class']}", 1, 0, 'L', True)
        self.cell(64, 7, f" ROLL NO: {data['Roll No']}", 1, 0, 'L', True)
        self.cell(63, 7, f" SECTION: {data['Section']}", 1, 1, 'L', True)
        
        # Marks Table Header
        self.ln(2)
        self.set_fill_color(50, 50, 50)
        self.cell(110, 8, "SUBJECT", 1, 0, 'C', True)
        self.cell(40, 8, "TOTAL MARKS", 1, 0, 'C', True)
        self.cell(40, 8, "OBTAINED", 1, 1, 'C', True)
        
        # Marks Data
        self.set_text_color(0, 0, 0)
        self.set_font("Arial", '', 9)
        grand_total = 0
        max_total = len(SUBJECTS) * 50
        
        for sub in SUBJECTS:
            val = int(data[sub])
            grand_total += val
            self.cell(110, 8, f" {sub}", 1)
            self.cell(40, 8, "50", 1, 0, 'C')
            self.cell(40, 8, str(val), 1, 1, 'C')
            
        # Grand Total Row
        self.set_font("Arial", 'B', 10)
        self.cell(110, 8, " GRAND TOTAL", 1)
        self.cell(40, 8, str(max_total), 1, 0, 'C')
        self.cell(40, 8, str(grand_total), 1, 1, 'C')
        
        # Bottom Metrics
        self.ln(2)
        perc = (grand_total / max_total) * 100
        grade = get_grade(perc)
        self.set_font("Arial", 'B', 8)
        self.cell(47, 8, f"PERCENTAGE: {perc:.1f}%", 1, 0, 'C')
        self.cell(47, 8, "POSITION: ---", 1, 0, 'C')
        self.cell(47, 8, f"PERFORMANCE: {get_performance(grade)}", 1, 0, 'C')
        self.cell(49, 8, f"FINAL GRADE: {grade}", 1, 1, 'C')
        
        # Footer
        self.ln(30)
        self.set_font("Arial", 'I', 10)
        self.cell(190, 5, '"Education is the most powerful weapon which you can use to change the world."', ln=True, align='C')
        self.cell(190, 5, '"The beautiful thing about learning is that no one can take it away from you."', ln=True, align='C')
        
        self.ln(15)
        self.set_font("Arial", 'B', 9)
        self.cell(95, 10, "_______________________", 0, 0, 'C')
        self.cell(95, 10, "_______________________", 0, 1, 'C')
        self.cell(95, 5, "CLASS TEACHER", 0, 0, 'C')
        self.cell(95, 5, "SENIOR HEAD MASTER (SAFDAR JAVED)", 0, 1, 'C')
        
        self.ln(5)
        self.set_font("Arial", '', 8)
        self.cell(190, 10, f"Result Declaration Date: 31-03-2026", 0, 0, 'R')

# --- MAIN INTERFACE ---
st.title("🏫 GHS Bhutta Mohabbat - Result System")

# Authentication
if 'authenticated' not in st.session_state:
    with st.sidebar:
        st.subheader("Login")
        pwd = st.text_input("Access Password", type="password")
        if st.button("Connect"):
            if pwd == "ghs123": # Use this password
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Access Denied")
    st.info("👈 Please login from the sidebar to manage marks.")
    st.stop()

# Dashboard Tabs
tab_entry, tab_manage, tab_bulk = st.tabs(["📊 Daily Marks Entry", "👥 Student Database", "🖨️ Bulk Generation"])

with tab_entry:
    st.header("Daily Subject Grading")
    col_a, col_b = st.columns([2, 1])
    
    with col_b:
        target_sub = st.selectbox("Select Subject to Update", SUBJECTS)
        st.warning("Max marks for all subjects is 50 as per school policy.")

    # Data Editor for Marks
    df_marks = st.session_state.students_db.copy()
    edited_marks = st.data_editor(
        df_marks[["Roll No", "Name", "Section", target_sub]],
        use_container_width=True,
        disabled=["Roll No", "Name", "Section"],
        key="marks_editor"
    )
    
    if st.button("💾 Save & Sync Data", type="primary"):
        st.session_state.students_db.update(edited_marks)
        st.success(f"Daily marks for {target_sub} updated for all students!")

with tab_manage:
    st.header("Student Information")
    with st.expander("➕ Add New Student to Session"):
        with st.form("new_student"):
            c1, c2, c3 = st.columns(3)
            r = c1.number_input("Roll No", min_value=1)
            n = c2.text_input("Full Name")
            f = c3.text_input("Father Name")
            c4, c5 = st.columns(2)
            cls = c4.selectbox("Class", ["9", "10"])
            sec = c5.selectbox("Section", ["A", "B", "C"])
            
            if st.form_submit_button("Register Student"):
                new_data = {"Roll No": r, "Name": n, "Father Name": f, "Class": cls, "Section": sec, **{s: 0 for s in SUBJECTS}}
                st.session_state.students_db = pd.concat([st.session_state.students_db, pd.DataFrame([new_data])], ignore_index=True)
                st.rerun()
    
    st.dataframe(st.session_state.students_db, use_container_width=True)

with tab_bulk:
    st.header("Bulk Result Generation")
    st.write("Click below to generate a single PDF containing report cards for ALL students currently in the system.")
    
    if st.button("🚀 Prepare Bulk PDF (All Students)"):
        pdf = ResultPDF()
        for index, row in st.session_state.students_db.iterrows():
            pdf.draw_report_card(row)
        
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.download_button(
            label="⬇️ Download All Result Cards",
            data=pdf_bytes,
            file_name=f"GHS_Results_Bulk_2026.pdf",
            mime="application/pdf"
        )

# Sidebar Info
st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())
st.sidebar.markdown("---")
st.sidebar.image("https://img.icons8.com/fluency/96/school.png")
st.sidebar.write("**Govt. High School Bhutta Mohabbat**")
st.sidebar.caption("Result Declaration System v2.0")
