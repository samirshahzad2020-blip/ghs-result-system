import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- APP CONFIG ---
st.set_page_config(page_title="GHS Result System", layout="wide", page_icon="🏫")

# --- CONSTANTS ---
DEFAULT_SUBJECTS = [
    "English", "Urdu", "Mathematics", "Islamiat", 
    "Science", "Social Study", "Computer", "Tajuma-tu-Quran"
]
# Updated classes from Nursery to 8th
CLASSES = ["Nursery", "K.G", "1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"]
SECTIONS = ["A", "B", "C"]

# --- SESSION STATE INITIALIZATION ---
if 'students_db' not in st.session_state:
    # Starting with an empty database structure
    st.session_state.students_db = pd.DataFrame(columns=[
        "Roll No", "Name", "Father Name", "Class", "Section"
    ] + DEFAULT_SUBJECTS + [f"Total_{sub}" for sub in DEFAULT_SUBJECTS])

# --- HELPER FUNCTIONS ---
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

# --- PDF GENERATOR ---
class ResultPDF(FPDF):
    def draw_report_card(self, data, active_subjects, logo_path=None):
        self.add_page()
        # Outer Borders
        self.set_line_width(0.5)
        self.rect(5, 5, 200, 287)
        self.set_line_width(0.3)
        self.rect(7, 7, 196, 283)
        
        if logo_path:
            try:
                self.image(logo_path, 12, 12, 25)
            except:
                pass
        
        # Header Info
        self.set_font("Helvetica", 'B', 8)
        self.cell(190, 4, "SCHOOL EDUCATION DEPARTMENT", ln=True, align='C')
        self.set_font("Helvetica", 'B', 14)
        self.cell(190, 7, "GOVT. HIGH SCHOOL BHUTTA MOHABBAT", ln=True, align='C')
        self.set_font("Helvetica", 'B', 9)
        self.cell(190, 5, "EMIS CODE: 39310025 | DISTRICT OKARA", ln=True, align='C')
        self.ln(2)
        
        self.set_font("Helvetica", 'B', 18)
        self.set_text_color(70, 130, 180) 
        self.cell(190, 10, "STUDENT REPORT CARD", ln=True, align='C')
        self.set_text_color(0, 0, 0)
        
        self.set_font("Helvetica", 'B', 10)
        self.cell(190, 8, "Session 2025-2026", ln=True)
        
        # Student Details Table
        self.set_fill_color(180, 200, 220)
        self.set_font("Helvetica", 'B', 9)
        self.cell(95, 8, f" NAME: {str(data['Name']).upper()}", 1, 0, 'L', True)
        self.cell(95, 8, f" FATHER NAME: {str(data['Father Name']).upper()}", 1, 1, 'L', True)
        self.cell(63, 8, f" CLASS: {data['Class']}", 1, 0, 'L', True)
        self.cell(64, 8, f" ROLL NO: {data['Roll No']}", 1, 0, 'L', True)
        self.cell(63, 8, f" SECTION: {data['Section']}", 1, 1, 'L', True)
        
        # Marks Table
        self.ln(3)
        self.set_fill_color(40, 40, 40)
        self.set_text_color(255, 255, 255)
        self.cell(110, 9, "SUBJECT", 1, 0, 'C', True)
        self.cell(40, 9, "TOTAL MARKS", 1, 0, 'C', True)
        self.cell(40, 9, "OBTAINED", 1, 1, 'C', True)
        
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", '', 10)
        grand_total_obtained = 0
        grand_total_max = 0
        
        for sub in active_subjects:
            obtained = int(data.get(sub, 0))
            total_max = int(data.get(f"Total_{sub}", 50))
            grand_total_obtained += obtained
            grand_total_max += total_max
            self.cell(110, 8, f" {sub}", 1)
            self.cell(40, 8, str(total_max), 1, 0, 'C')
            self.cell(40, 8, str(obtained), 1, 1, 'C')
            
        # Total row
        self.set_font("Helvetica", 'B', 10)
        self.cell(110, 9, " GRAND TOTAL", 1)
        self.cell(40, 9, str(grand_total_max), 1, 0, 'C')
        self.cell(40, 9, str(grand_total_obtained), 1, 1, 'C')
        
        # Result metrics
        self.ln(4)
        perc = (grand_total_obtained / grand_total_max) * 100 if grand_total_max > 0 else 0
        grade = get_grade(perc)
        self.set_font("Helvetica", 'B', 8)
        self.cell(47, 10, f"PERCENTAGE: {perc:.1f}%", 1, 0, 'C')
        self.cell(47, 10, "POSITION: ---", 1, 0, 'C')
        self.cell(47, 10, f"PERFORMANCE: {get_performance(grade)}", 1, 0, 'C')
        self.cell(49, 10, f"FINAL GRADE: {grade}", 1, 1, 'C')
        
        # Footer Quotes
        self.ln(20)
        self.set_font("Helvetica", 'I', 10)
        self.multi_cell(190, 6, '"Education is the most powerful weapon which you can use to change the world."\n"The beautiful thing about learning is that no one can take it away from you."', align='C')
        
        # Signatures
        self.ln(15)
        self.set_font("Helvetica", 'B', 9)
        self.cell(95, 10, "_______________________", 0, 0, 'C')
        self.cell(95, 10, "_______________________", 0, 1, 'C')
        self.cell(95, 5, "CLASS TEACHER", 0, 0, 'C')
        self.cell(95, 5, "SENIOR HEAD MASTER (SAFDAR JAVED)", 0, 1, 'C')
        
        self.ln(5)
        self.set_font("Helvetica", '', 8)
        self.cell(190, 10, "Result Declaration Date: 31-03-2026", 0, 0, 'R')

# --- UI INTERFACE ---
st.title("🛡️ GHS Management Portal")

with st.sidebar:
    st.header("Global Filters")
    # 1. Class Selection (Nursery to 8th)
    active_class = st.selectbox("Current Working Class", CLASSES)
    
    st.divider()
    # 2. Subject Selection with Check/Uncheck All
    st.subheader("Manage Subjects")
    
    col_t1, col_t2 = st.columns(2)
    if col_t1.button("Check All"):
        for sub in DEFAULT_SUBJECTS:
            st.session_state[f"sub_{sub}"] = True
    if col_t2.button("Uncheck All"):
        for sub in DEFAULT_SUBJECTS:
            st.session_state[f"sub_{sub}"] = False

    selected_subjects = []
    for sub in DEFAULT_SUBJECTS:
        # Provide default 'True' if state doesn't exist
        if st.checkbox(sub, value=st.session_state.get(f"sub_{sub}", True), key=f"sub_{sub}"):
            selected_subjects.append(sub)
            
    st.divider()
    school_logo = st.file_uploader("School Logo", type=['png', 'jpg', 'jpeg'])

    if 'auth' not in st.session_state:
        pwd = st.text_input("Access Key", type="password")
        if st.button("Login"):
            if pwd == "ghs123":
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Invalid Key")
        st.stop()
    
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# --- FILTER DATA BY CLASS ---
filtered_db = st.session_state.students_db[st.session_state.students_db["Class"] == active_class]

# Main Tabs
tab_marks, tab_db, tab_bulk = st.tabs(["🖊️ Marks Entry", "📋 Student Directory", "🖨️ Reports"])

with tab_marks:
    st.header(f"Grading Panel - Class {active_class}")
    
    if filtered_db.empty:
        st.info(f"No students found in Class {active_class}. Register them in Student Directory.")
    else:
        student_to_grade = st.selectbox("Select Student", filtered_db["Name"].unique())
        
        # Locate correct index in global DB
        idx = st.session_state.students_db[(st.session_state.students_db["Name"] == student_to_grade) & 
                                          (st.session_state.students_db["Class"] == active_class)].index[0]
        curr_data = st.session_state.students_db.loc[idx]
        
        with st.form("marks_entry_form"):
            st.write(f"Updating: **{curr_data['Name']}** (Roll No: {curr_data['Roll No']})")
            for sub in selected_subjects:
                c1, c2 = st.columns(2)
                # Ensure we handle missing columns gracefully
                val_obt = curr_data.get(sub, 0)
                val_tot = curr_data.get(f"Total_{sub}", 50)
                
                obtained = c1.number_input(f"{sub} Obtained", min_value=0, max_value=500, value=int(val_obt if pd.notnull(val_obt) else 0))
                total_m = c2.number_input(f"{sub} Total Marks", min_value=1, max_value=500, value=int(val_tot if pd.notnull(val_tot) else 50))
                
                # Update Session State
                st.session_state.students_db.at[idx, sub] = obtained
                st.session_state.students_db.at[idx, f"Total_{sub}"] = total_m
            
            if st.form_submit_button("Save Student Marks"):
                st.success(f"Marks updated for {student_to_grade}!")

with tab_db:
    st.header(f"Class {active_class} Directory")
    
    with st.expander(f"➕ Add Student to Class {active_class}"):
        with st.form("reg_form"):
            c1, c2, c3 = st.columns(3)
            r = c1.number_input("Roll No", min_value=1)
            n = c2.text_input("Full Name")
            f = c3.text_input("Father Name")
            sc = st.selectbox("Section", SECTIONS)
            
            if st.form_submit_button("Register Student"):
                new_row = {
                    "Roll No": r, "Name": n, "Father Name": f, 
                    "Class": active_class, "Section": sc, 
                    **{s: 0 for s in DEFAULT_SUBJECTS}, 
                    **{f"Total_{s}": 50 for s in DEFAULT_SUBJECTS}
                }
                st.session_state.students_db = pd.concat([st.session_state.students_db, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"Added {n} to Class {active_class}")
                st.rerun()
    
    st.dataframe(filtered_db[["Roll No", "Name", "Father Name", "Section"]], use_container_width=True)

with tab_bulk:
    st.header(f"Generate Reports (Class {active_class})")
    
    if filtered_db.empty:
        st.error("No data available to print for this class.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Individual Result")
            print_target = st.selectbox("Choose Student", filtered_db["Name"])
            if st.button("Generate Card"):
                row_data = filtered_db[filtered_db["Name"] == print_target].iloc[0]
                pdf = ResultPDF()
                pdf.draw_report_card(row_data, selected_subjects, logo_path=school_logo if school_logo else None)
                pdf_bytes = pdf.output()
                st.download_button(label=f"⬇️ Download {print_target}'s Card", data=bytes(pdf_bytes), file_name=f"Result_{print_target}.pdf", mime="application/pdf")
                
        with col2:
            st.subheader("Bulk Class Results")
            st.write(f"Generate result cards for all {len(filtered_db)} students in Class {active_class}.")
            if st.button(f"Prepare Bulk PDF"):
                pdf = ResultPDF()
                # Sort by roll no
                sorted_class = filtered_db.sort_values("Roll No")
                for _, row in sorted_class.iterrows():
                    pdf.draw_report_card(row, selected_subjects, logo_path=school_logo if school_logo else None)
                
                bulk_bytes = pdf.output()
                st.download_button(label=f"⬇️ Download Bulk PDF", data=bytes(bulk_bytes), file_name=f"Class_{active_class}_Results.pdf", mime="application/pdf")
