import streamlit as st
import pandas as pd
from fpdf import FPDF
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- APP CONFIG ---
st.set_page_config(page_title="GHS Result System", layout="wide", page_icon="🏫")

# --- DATABASE SETUP ---
@st.cache_resource
def init_db():
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets:
                key_dict = json.loads(st.secrets["firebase"]["textkey"])
                if "private_key" in key_dict:
                    key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
                creds = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(creds)
                return firestore.client()
        except: return None
    return firestore.client()

db = init_db()
# Cloud Path remains exactly the same to protect your data
COL_PATH = ["artifacts", "ghs-bhutta-mohabbat-v10", "public", "data", "students"]

# --- CONSTANTS ---
CLASSES = ["Nursery", "K.G", "1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"]
SECTIONS = ["A", "B"]
SUBJECTS = ["English", "Urdu", "Mathematics", "Islamiat", "Science", "Social Study", "Computer", "Tajuma-tu-Quran"]

def get_grade_perf(p):
    """Returns (Grade, Performance) based on percentage"""
    if p >= 80: return "A+", "Excellent"
    elif p >= 70: return "A", "Very Good"
    elif p >= 60: return "B", "Good"
    elif p >= 50: return "C", "Satisfactory"
    elif p >= 40: return "D", "Fair"
    else: return "F", "Poor / Fail"

# --- DATA FUNCTIONS ---
def get_students():
    if db:
        try:
            docs = list(db.collection(*COL_PATH).stream())
            return pd.DataFrame([doc.to_dict() for doc in docs]) if docs else pd.DataFrame()
        except: return pd.DataFrame()
    return st.session_state.get('local_db', pd.DataFrame())

def save_student(data):
    if db:
        try:
            uid = f"{data['Class']}_{data['Section']}_{data['Roll No']}".replace(" ", "_")
            db.collection(*COL_PATH).document(uid).set(data)
            return True
        except: return False
    else:
        if 'local_db' not in st.session_state: st.session_state.local_db = pd.DataFrame()
        st.session_state.local_db = pd.concat([st.session_state.local_db, pd.DataFrame([data])]).drop_duplicates(['Class', 'Section', 'Roll No'], keep='last')
        return True

def delete_student(cls, sec, roll):
    if db:
        try:
            uid = f"{cls}_{sec}_{roll}".replace(" ", "_")
            db.collection(*COL_PATH).document(uid).delete()
        except: pass
    else:
        if 'local_db' in st.session_state:
            st.session_state.local_db = st.session_state.local_db[~((st.session_state.local_db['Class']==cls) & (st.session_state.local_db['Section']==sec) & (st.session_state.local_db['Roll No']==roll))]

# --- PDF ENGINES ---
class ResultPDF(FPDF):
    def draw(self, d, subs, logo):
        self.add_page()
        self.set_line_width(0.5); self.rect(5, 5, 200, 287); self.set_line_width(0.2); self.rect(7, 7, 196, 283)
        if logo:
            try: self.image(logo, 10, 10, 25)
            except: pass
        
        self.set_font("Helvetica", 'B', 8); self.cell(190, 4, "SCHOOL EDUCATION DEPARTMENT", ln=True, align='C')
        self.set_font("Helvetica", 'B', 14); self.cell(190, 7, "GOVT. HIGH SCHOOL BHUTTA MOHABBAT", ln=True, align='C')
        self.set_font("Helvetica", 'B', 9); self.cell(190, 5, "EMIS CODE: 39310025 | DISTRICT OKARA", ln=True, align='C')
        self.ln(2); self.set_font("Helvetica", 'B', 18); self.set_text_color(70, 130, 180); self.cell(190, 10, "STUDENT REPORT CARD", ln=True, align='C')
        self.set_text_color(0,0,0); self.set_font("Helvetica", 'B', 10); self.cell(190, 8, "Session 2025-2026", ln=True, align='C')
        
        self.set_fill_color(220, 230, 245); self.set_font("Helvetica", 'B', 9)
        self.cell(95, 8, f" NAME: {str(d['Name']).upper()}", 1, 0, 'L', True); self.cell(95, 8, f" FATHER: {str(d['Father Name']).upper()}", 1, 1, 'L', True)
        self.cell(63, 8, f" CLASS: {d['Class']}", 1, 0, 'L', True); self.cell(64, 8, f" SECTION: {d.get('Section','A')}", 1, 0, 'L', True); self.cell(63, 8, f" ROLL NO: {d['Roll No']}", 1, 1, 'L', True)
        
        self.ln(3); self.set_fill_color(50, 50, 50); self.set_text_color(255, 255, 255)
        self.cell(110, 9, "SUBJECT", 1, 0, 'C', True); self.cell(40, 9, "TOTAL", 1, 0, 'C', True); self.cell(40, 9, "OBTAINED", 1, 1, 'C', True)
        self.set_text_color(0, 0, 0); self.set_font("Helvetica", '', 10)
        
        obt_t, max_t = 0, 0
        for s in subs:
            o, t = int(d.get(s, 0)), int(d.get(f"Total_{s}", 50)); obt_t += o; max_t += t
            self.cell(110, 8, f" {s}", 1); self.cell(40, 8, str(t), 1, 0, 'C'); self.cell(40, 8, str(o), 1, 1, 'C')
        
        self.set_font("Helvetica", 'B', 10); self.cell(110, 9, " GRAND TOTAL", 1); self.cell(40, 9, str(max_t), 1, 0, 'C'); self.cell(40, 9, str(obt_t), 1, 1, 'C')
        
        self.ln(4)
        perc = (obt_t / max_t * 100) if max_t > 0 else 0
        grade, perf = get_grade_perf(perc)
        
        self.set_font("Helvetica", 'B', 8)
        self.cell(47, 10, f"PERC: {perc:.1f}%", 1, 0, 'C'); self.cell(47, 10, f"POS: {d.get('Position', '---')}", 1, 0, 'C')
        self.cell(47, 10, f"PERF: {perf}", 1, 0, 'C'); self.cell(49, 10, f"GRADE: {grade}", 1, 1, 'C')
        
        self.ln(15); self.set_font("Helvetica", 'I', 10); 
        self.multi_cell(190, 6, '"Education is the most powerful weapon which you can use to change the world."\n"The beautiful thing about learning is that no one can take it away from you."', align='C')
        self.ln(15); self.set_font("Helvetica", 'B', 9); self.cell(95, 10, "_______________________", 0, 0, 'C'); self.cell(95, 10, "_______________________", 0, 1, 'C')
        self.cell(95, 5, "CLASS TEACHER", 0, 0, 'C'); self.cell(95, 5, "SENIOR HEAD MASTER (SAFDAR JAVED)", 0, 1, 'C')
        self.ln(5); self.set_font("Helvetica", '', 8); self.cell(190, 10, "Result Date: 31-03-2026", 0, 0, 'R')

class AwardListPDF(FPDF):
    def draw(self, df_data, class_name, section_name):
        self.add_page()
        self.set_font("Helvetica", 'B', 14)
        self.cell(190, 10, "GOVT. HIGH SCHOOL BHUTTA MOHABBAT", ln=True, align='C')
        self.set_font("Helvetica", 'B', 12)
        self.cell(190, 8, f"AWARD LIST - CLASS {class_name} ({section_name})", ln=True, align='C')
        self.ln(5)
        # Table Headers
        self.set_fill_color(200, 200, 200)
        self.set_font("Helvetica", 'B', 10)
        self.cell(20, 10, "Roll No", 1, 0, 'C', True)
        self.cell(75, 10, "Student Name", 1, 0, 'C', True)
        self.cell(35, 10, "Total Marks", 1, 0, 'C', True)
        self.cell(35, 10, "Percentage", 1, 0, 'C', True)
        self.cell(25, 10, "Position", 1, 1, 'C', True)
        
        self.set_font("Helvetica", '', 10)
        for _, row in df_data.iterrows():
            self.cell(20, 8, str(row['Roll No']), 1, 0, 'C')
            self.cell(75, 8, f" {str(row['Name']).upper()}", 1, 0, 'L')
            self.cell(35, 8, str(int(row['Total_Obtained'])), 1, 0, 'C')
            self.cell(35, 8, f"{row['Percentage']:.1f}%", 1, 0, 'C')
            self.cell(25, 8, str(row['Position']), 1, 1, 'C')

# --- UI INTERFACE ---
if db: st.success("🟢 Permanent Cloud Storage Active")
else: st.warning("🔴 Temporary Mode (Update Secrets)")

with st.sidebar:
    st.header("Class Management")
    cl = st.selectbox("Select Class", CLASSES, key="sidebar_class")
    sc = st.selectbox("Select Section", SECTIONS, key="sidebar_section")
    st.divider()
    if st.button("Check All Subjects", key="btn_check_all"): 
        for s in SUBJECTS: st.session_state[f"s_{s}"] = True
    if st.button("Uncheck All Subjects", key="btn_uncheck_all"): 
        for s in SUBJECTS: st.session_state[f"s_{s}"] = False
    sel = [s for s in SUBJECTS if st.checkbox(s, value=st.session_state.get(f"s_{s}", True), key=f"s_{s}")]
    st.divider(); logo = st.file_uploader("Upload School Logo", type=['png', 'jpg'], key="logo_upload")
    if 'auth' not in st.session_state:
        pw = st.text_input("Login Key", type="password", key="login_pw")
        if st.button("Login", key="login_btn"):
            if pw == "ghs123": st.session_state.auth = True; st.rerun()
            else: st.error("Wrong Key")
        st.stop()
    if st.button("Logout", key="logout_btn"): st.session_state.clear(); st.rerun()

# --- MAIN APP ---
df = get_students()
if not df.empty:
    fil = df[(df["Class"] == cl) & (df["Section"] == sc)].copy()
else:
    fil = pd.DataFrame()

# Pre-calculate Ranks for the current class
if not fil.empty:
    fil['Total_Obtained'] = fil[sel].apply(pd.to_numeric).sum(axis=1)
    # Assume 50 as total marks per subject for percentage calculation
    total_max_marks = len(sel) * 50
    fil['Percentage'] = (fil['Total_Obtained'] / total_max_marks * 100) if total_max_marks > 0 else 0
    fil['Position'] = fil['Total_Obtained'].rank(ascending=False, method='min').astype(int)
    fil = fil.sort_values("Roll No")

tab1, tab2, tab3 = st.tabs(["🖊️ Marks Entry", "📋 Student Directory", "🖨️ Print Results"])

with tab1:
    st.header(f"Grading - {cl} ({sc})")
    if fil.empty: st.info(f"Class {cl} Section {sc} empty.")
    else:
        sn = st.selectbox("Select Student", fil["Name"].unique(), key="marks_student_select")
        student_row = fil[fil["Name"] == sn].iloc[0].to_dict()
        with st.form(f"marks_form_{cl}_{sc}_{sn}"):
            for s in sel:
                c1, c2 = st.columns(2)
                student_row[s] = c1.number_input(f"{s} Obtained", 0, 500, int(student_row.get(s, 0)), key=f"obt_{s}_{sn}")
                student_row[f"Total_{s}"] = c2.number_input(f"{s} Total", 1, 500, int(student_row.get(f"Total_{s}", 50)), key=f"tot_{s}_{sn}")
            if st.form_submit_button("Save Marks Permanently"):
                if save_student(student_row): st.success("Cloud saved!"); st.rerun()

with tab2:
    st.header(f"Directory - {cl} ({sc})")
    with st.expander(f"➕ Add Student to {cl} Section {sc}"):
        with st.form("add_student_form"):
            r, n, f = st.columns(3)
            roll = r.number_input("Roll No", 1, key="add_roll")
            name = n.text_input("Full Name", key="add_name")
            fat = f.text_input("Father Name", key="add_fat")
            if st.form_submit_button("Register"):
                save_student({"Roll No": roll, "Name": name, "Father Name": fat, "Class": cl, "Section": sc, **{s: 0 for s in SUBJECTS}, **{f"Total_{s}": 50 for s in SUBJECTS}})
                st.rerun()
    if not fil.empty:
        st.write("Current Students:")
        for i, row in fil.sort_values("Roll No").iterrows():
            c1, c2 = st.columns([5, 1])
            c1.write(f"**Roll {row['Roll No']}**: {row['Name']}")
            if c2.button("🗑️", key=f"del_{cl}_{sc}_{row['Roll No']}"):
                delete_student(cl, sc, row['Roll No']); st.rerun()

with tab3:
    st.header(f"Print - {cl} ({sc})")
    if fil.empty: st.error("No data.")
    else:
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            st.subheader("Individual Cards")
            pn = st.selectbox("Select Student", fil["Name"].unique(), key="print_student_select")
            if st.button("Generate Single Card", key="btn_single_pdf"):
                pdf = ResultPDF(); pdf.draw(fil[fil["Name"] == pn].iloc[0].to_dict(), sel, logo)
                st.download_button(f"Download {pn}.pdf", bytes(pdf.output()), f"{pn}.pdf", "application/pdf")
        
        with c_p2:
            st.subheader("Class Summary")
            if st.button("Generate Bulk Result PDF", key="btn_bulk_pdf"):
                pdf = ResultPDF()
                for _, r in fil.sort_values("Roll No").iterrows(): pdf.draw(r.to_dict(), sel, logo)
                st.download_button("Download All Results", bytes(pdf.output()), f"Class_{cl}_{sc}_Results.pdf", "application/pdf")
            
            st.divider()
            if st.button("Generate Award List (Gazette)", key="btn_award_list"):
                pdf_aw = AwardListPDF()
                pdf_aw.draw(fil, cl, sc)
                st.download_button(f"Download_Award_List_{cl}_{sc}.pdf", bytes(pdf_aw.output()), f"AwardList_{cl}_{sc}.pdf", "application/pdf")
