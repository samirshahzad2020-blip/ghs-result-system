import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- APP CONFIG ---
st.set_page_config(page_title="GHS Result System", layout="wide", page_icon="🏫")

# --- FIREBASE PERMANENT STORAGE SETUP ---
# Path Rule: /artifacts/{appId}/public/data/{collectionName}
APP_ID = "ghs-bhutta-mohabbat-v2"

def init_firebase():
    if not firebase_admin._apps:
        try:
            # On Streamlit Cloud, add your Firebase Service Account JSON to Secrets
            if "firebase" in st.secrets:
                key_dict = json.loads(st.secrets["firebase"]["textkey"])
                creds = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(creds)
            else:
                return None
        except Exception as e:
            st.error(f"Firebase Init Error: {e}")
            return None
    return firestore.client()

db = init_firebase()

# --- CONSTANTS (UNCHANGED) ---
DEFAULT_SUBJECTS = [
    "English", "Urdu", "Mathematics", "Islamiat", 
    "Science", "Social Study", "Computer", "Tajuma-tu-Quran"
]
CLASSES = ["Nursery", "K.G", "1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"]
SECTIONS = ["A", "B", "C"]

# --- DATA PERSISTENCE FUNCTIONS ---
def get_students_from_cloud():
    if db is None:
        return pd.DataFrame(columns=["Roll No", "Name", "Father Name", "Class", "Section"])
    
    # Simple query as per Rule 2
    docs = db.collection("artifacts", APP_ID, "public", "data", "students").stream()
    data = []
    for doc in docs:
        item = doc.to_dict()
        item["doc_id"] = doc.id
        data.append(item)
    
    if not data:
        return pd.DataFrame(columns=["Roll No", "Name", "Father Name", "Class", "Section"])
    return pd.DataFrame(data)

def save_student_to_cloud(student_data):
    if db:
        # Create a unique ID based on Class and Roll No
        uid = f"{student_data['Class']}_{student_data['Roll No']}".replace(" ", "_")
        db.collection("artifacts", APP_ID, "public", "data", "students").document(uid).set(student_data)

def delete_student_from_cloud(doc_id):
    if db:
        db.collection("artifacts", APP_ID, "public", "data", "students").document(doc_id).delete()

# --- PDF GENERATOR (MATCHING PREVIOUS DESIGN) ---
class ResultPDF(FPDF):
    def draw_report_card(self, data, active_subjects, logo_path=None):
        self.add_page()
        self.set_line_width(0.5)
        self.rect(5, 5, 200, 287)
        self.set_line_width(0.3)
        self.rect(7, 7, 196, 283)
        
        if logo_path:
            try: self.image(logo_path, 12, 12, 25)
            except: pass
        
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
        self.cell(190, 8, "Session 2025-2026", ln=True, align='C')
        
        self.set_fill_color(180, 200, 220)
        self.set_font("Helvetica", 'B', 9)
        self.cell(95, 8, f" NAME: {str(data['Name']).upper()}", 1, 0, 'L', True)
        self.cell(95, 8, f" FATHER NAME: {str(data['Father Name']).upper()}", 1, 1, 'L', True)
        self.cell(63, 8, f" CLASS: {data['Class']}", 1, 0, 'L', True)
        self.cell(64, 8, f" ROLL NO: {data['Roll No']}", 1, 0, 'L', True)
        self.cell(63, 8, f" SECTION: {data['Section']}", 1, 1, 'L', True)
        
        self.ln(3)
        self.set_fill_color(40, 40, 40)
        self.set_text_color(255, 255, 255)
        self.cell(110, 9, "SUBJECT", 1, 0, 'C', True)
        self.cell(40, 9, "TOTAL MARKS", 1, 0, 'C', True)
        self.cell(40, 9, "OBTAINED", 1, 1, 'C', True)
        
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", '', 10)
        grand_total_obt = 0
        grand_total_max = 0
        
        for sub in active_subjects:
            obt = int(data.get(sub, 0))
            tot = int(data.get(f"Total_{sub}", 50))
            grand_total_obt += obt
            grand_total_max += tot
            self.cell(110, 8, f" {sub}", 1)
            self.cell(40, 8, str(tot), 1, 0, 'C')
            self.cell(40, 8, str(obt), 1, 1, 'C')
            
        self.set_font("Helvetica", 'B', 10)
        self.cell(110, 9, " GRAND TOTAL", 1)
        self.cell(40, 9, str(grand_total_max), 1, 0, 'C')
        self.cell(40, 9, str(grand_total_obt), 1, 1, 'C')
        
        self.ln(4)
        perc = (grand_total_obt / grand_total_max * 100) if grand_total_max > 0 else 0
        self.set_font("Helvetica", 'B', 8)
        self.cell(47, 10, f"PERCENTAGE: {perc:.1f}%", 1, 0, 'C')
        self.cell(47, 10, "POSITION: ---", 1, 0, 'C')
        self.cell(47, 10, "PERFORMANCE: ---", 1, 0, 'C')
        self.cell(49, 10, "FINAL GRADE: ---", 1, 1, 'C')
        
        self.ln(20)
        self.set_font("Helvetica", 'I', 10)
        self.multi_cell(190, 6, '"Education is the most powerful weapon which you can use to change the world."\n"The beautiful thing about learning is that no one can take it away from you."', align='C')
        
        self.ln(15)
        self.set_font("Helvetica", 'B', 9)
        self.cell(95, 10, "_______________________", 0, 0, 'C')
        self.cell(95, 10, "_______________________", 0, 1, 'C')
        self.cell(95, 5, "CLASS TEACHER", 0, 0, 'C')
        self.cell(95, 5, "SENIOR HEAD MASTER (SAFDAR JAVED)", 0, 1, 'C')
        
        self.set_font("Helvetica", '', 8)
        self.ln(5)
        self.cell(190, 10, "Result Declaration Date: 31-03-2026", 0, 0, 'R')

# --- UI INTERFACE ---
st.title("🛡️ GHS Management Portal (Cloud Saving)")

if db is None:
    st.warning("⚠️ Cloud Storage not configured. Please add Firebase secrets to Streamlit Cloud Settings.")

with st.sidebar:
    st.header("Global Filters")
    active_class = st.selectbox("Current Working Class", CLASSES)
    
    st.divider()
    st.subheader("Manage Subjects")
    col_t1, col_t2 = st.columns(2)
    if col_t1.button("Check All"):
        for sub in DEFAULT_SUBJECTS: st.session_state[f"sub_{sub}"] = True
    if col_t2.button("Uncheck All"):
        for sub in DEFAULT_SUBJECTS: st.session_state[f"sub_{sub}"] = False

    selected_subjects = []
    for sub in DEFAULT_SUBJECTS:
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
            else: st.error("Invalid Key")
        st.stop()
    
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# Load Data from Cloud (Permanent)
students_df = get_students_from_cloud()
filtered_db = students_df[students_df["Class"] == active_class]

tab_marks, tab_db, tab_bulk = st.tabs(["🖊️ Marks Entry", "📋 Student Directory", "🖨️ Reports"])

with tab_marks:
    st.header(f"Grading Panel - Class {active_class}")
    if filtered_db.empty:
        st.info(f"No students found in Class {active_class}.")
    else:
        student_name = st.selectbox("Select Student", filtered_db["Name"].unique())
        student_data = filtered_db[filtered_db["Name"] == student_name].iloc[0].to_dict()
        
        with st.form("marks_entry_form"):
            st.write(f"Updating: **{student_name}** (Roll No: {student_data['Roll No']})")
            for sub in selected_subjects:
                c1, c2 = st.columns(2)
                student_data[sub] = c1.number_input(f"{sub} Obtained", 0, 500, int(student_data.get(sub, 0)))
                student_data[f"Total_{sub}"] = c2.number_input(f"{sub} Total Marks", 1, 500, int(student_data.get(f"Total_{sub}", 50)))
            
            if st.form_submit_button("💾 Save Marks to Cloud"):
                save_student_to_cloud(student_data)
                st.success(f"Marks for {student_name} saved forever!")
                st.rerun()

with tab_db:
    st.header(f"Class {active_class} Directory")
    with st.expander(f"➕ Add Student to Class {active_class}"):
        with st.form("reg_form"):
            c1, c2, c3 = st.columns(3)
            r = c1.number_input("Roll No", min_value=1)
            n = c2.text_input("Full Name")
            f = c3.text_input("Father Name")
            sc = st.selectbox("Section", SECTIONS)
            if st.form_submit_button("Register Student Permanently"):
                new_row = {
                    "Roll No": r, "Name": n, "Father Name": f, "Class": active_class, "Section": sc,
                    **{s: 0 for s in DEFAULT_SUBJECTS}, **{f"Total_{s}": 50 for s in DEFAULT_SUBJECTS}
                }
                save_student_to_cloud(new_row)
                st.success(f"Registered {n} in Cloud Storage!")
                st.rerun()
    
    st.divider()
    st.subheader("Manage Existing Students")
    if filtered_db.empty:
        st.write("Directory empty.")
    else:
        for index, row in filtered_db.iterrows():
            col_info, col_del = st.columns([4, 1])
            with col_info:
                st.write(f"**Roll No:** {row['Roll No']} | **Name:** {row['Name']}")
            with col_del:
                # doc_id is the unique key in firestore
                if st.button(f"🗑️ Delete", key=f"del_{row.get('doc_id', index)}"):
                    delete_student_from_cloud(row['doc_id'])
                    st.rerun()
    
    st.divider()
    st.dataframe(filtered_db[["Roll No", "Name", "Father Name", "Section"]], use_container_width=True)

with tab_bulk:
    st.header(f"Generate Reports")
    if filtered_db.empty:
        st.error("No data available.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Individual Print")
            print_target = st.selectbox("Choose Student", filtered_db["Name"])
            if st.button("Generate Card"):
                row_data = filtered_db[filtered_db["Name"] == print_target].iloc[0]
                pdf = ResultPDF()
                pdf.draw_report_card(row_data, selected_subjects, logo_path=school_logo)
                st.download_button(f"Download {print_target}.pdf", pdf.output(), f"{print_target}.pdf", "application/pdf")
        with col2:
            st.subheader("Bulk Print")
            if st.button(f"Prepare Bulk PDF"):
                pdf = ResultPDF()
                for _, row in filtered_db.sort_values("Roll No").iterrows():
                    pdf.draw_report_card(row, selected_subjects, logo_path=school_logo)
                st.download_button("Download All Results", pdf.output(), "Bulk_Results.pdf", "application/pdf")
