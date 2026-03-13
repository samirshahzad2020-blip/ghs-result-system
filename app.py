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
# Cloud Path: artifacts/ghs-bhutta-mohabbat/public/data/students
COL_PATH = ["artifacts", "ghs-bhutta-mohabbat", "public", "data", "students"]

# --- CONSTANTS ---
CLASSES = ["Nursery", "K.G", "1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"]
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
            uid = f"{data['Class']}_{data['Roll No']}".replace(" ", "_")
            db.collection(*COL_PATH).document(uid).set(data)
            return True
        except: return False
    else:
        if 'local_db' not in st.session_state: st.session_state.local_db = pd.DataFrame()
        st.session_state.local_db = pd.concat([st.session_state.local_db, pd.DataFrame([data])]).drop_duplicates(['Class', 'Roll No'], keep='last')
        return True

def delete_student(cls, roll):
    if db:
        try:
            uid = f"{cls}_{roll}".replace(" ", "_")
            db.collection(*COL_PATH).document(uid).delete()
        except: pass
    else:
        if 'local_db' in st.session_state:
            st.session_state.local_db = st.session_state.local_db[~((st.session_state.local_db['Class']==cls) & (st.session_state.local_db['Roll No']==roll))]

# --- PDF ENGINE ---
class ResultPDF(FPDF):
    def draw(self, d, subs, logo):
        self.add_page()
        # Page Borders
        self.set_line_width(0.5); self.rect(5, 5, 200, 287); self.set_line_width(0.2); self.rect(7, 7, 196, 283)
        if logo:
            try: self.image(logo, 10, 10, 25)
            except: pass
        
        # Header Info
        self.set_font("Helvetica", 'B', 8); self.cell(190, 4, "SCHOOL EDUCATION DEPARTMENT", ln=True, align='C')
        self.set_font("Helvetica", 'B', 14); self.cell(190, 7, "GOVT. HIGH SCHOOL BHUTTA MOHABBAT", ln=True, align='C')
        self.set_font("Helvetica", 'B', 9); self.cell(190, 5, "EMIS CODE: 39310025 | DISTRICT OKARA", ln=True, align='C')
        self.ln(2); self.set_font("Helvetica", 'B', 18); self.set_text_color(70, 130, 180); self.cell(190, 10, "STUDENT REPORT CARD", ln=True, align='C')
        self.set_text_color(0,0,0); self.set_font("Helvetica", 'B', 10); self.cell(190, 8, "Session 2025-2026", ln=True, align='C')
        
        # Student Info Box
        self.set_fill_color(220, 230, 245); self.set_font("Helvetica", 'B', 9)
        self.cell(95, 8, f" NAME: {str(d['Name']).upper()}", 1, 0, 'L', True); self.cell(95, 8, f" FATHER: {str(d['Father Name']).upper()}", 1, 1, 'L', True)
        self.cell(63, 8, f" CLASS: {d['Class']}", 1, 0, 'L', True); self.cell(64, 8, f" ROLL: {d['Roll No']}", 1, 0, 'L', True); self.cell(63, 8, f" SEC: {d.get('Section','A')}", 1, 1, 'L', True)
        
        # Marks Table Header
        self.ln(3); self.set_fill_color(50, 50, 50); self.set_text_color(255, 255, 255); 
        self.cell(110, 9, "SUBJECT", 1, 0, 'C', True); self.cell(40, 9, "TOTAL", 1, 0, 'C', True); self.cell(40, 9, "OBTAINED", 1, 1, 'C', True)
        self.set_text_color(0, 0, 0); self.set_font("Helvetica", '', 10)
        
        # Table Rows
        obt_t, max_t = 0, 0
        for s in subs:
            o, t = int(d.get(s, 0)), int(d.get(f"Total_{s}", 50)); obt_t += o; max_t += t
            self.cell(110, 8, f" {s}", 1); self.cell(40, 8, str(t), 1, 0, 'C'); self.cell(40, 8, str(o), 1, 1, 'C')
        
        # Grand Total
        self.set_font("Helvetica", 'B', 10); self.cell(110, 9, " GRAND TOTAL", 1); self.cell(40, 9, str(max_t), 1, 0, 'C'); self.cell(40, 9, str(obt_t), 1, 1, 'C')
        
        # Grading Metrics (FIXED THE VALUEERROR HERE)
        self.ln(4)
        perc = (obt_t / max_t * 100) if max_t > 0 else 0
        grade, perf = get_grade_perf(perc)
        
        self.set_font("Helvetica", 'B', 8)
        self.cell(47, 10, f"PERC: {perc:.1f}%", 1, 0, 'C')
        self.cell(47, 10, "POS: ---", 1, 0, 'C')
        self.cell(47, 10, f"PERF: {perf}", 1, 0, 'C')
        self.cell(49, 10, f"GRADE: {grade}", 1, 1, 'C')
        
        # Footer
        self.ln(15); self.set_font("Helvetica", 'I', 10); 
        self.multi_cell(190, 6, '"Education is the most powerful weapon which you can use to change the world."\n"The beautiful thing about learning is that no one can take it away from you."', align='C')
        self.ln(15); self.set_font("Helvetica", 'B', 9); self.cell(95, 10, "_______________________", 0, 0, 'C'); self.cell(95, 10, "_______________________", 0, 1, 'C')
        self.cell(95, 5, "CLASS TEACHER", 0, 0, 'C'); self.cell(95, 5, "SENIOR HEAD MASTER (SAFDAR JAVED)", 0, 1, 'C')
        self.ln(5); self.set_font("Helvetica", '', 8); self.cell(190, 10, "Result Date: 31-03-2026", 0, 0, 'R')

# --- UI INTERFACE ---
if db: st.success("🟢 Permanent Cloud Storage Active")
else: st.warning("🔴 Temporary Mode (Update Secrets)")

with st.sidebar:
    cl = st.selectbox("Select Class", CLASSES); st.divider()
    if st.button("Check All Subjects"): 
        for s in SUBJECTS: st.session_state[f"s_{s}"] = True
    if st.button("Uncheck All Subjects"): 
        for s in SUBJECTS: st.session_state[f"s_{s}"] = False
    sel = [s for s in SUBJECTS if st.checkbox(s, value=st.session_state.get(f"s_{s}", True), key=f"s_{s}")]
    st.divider(); logo = st.file_uploader("Upload School Logo", type=['png', 'jpg'])
    if 'auth' not in st.session_state:
        pw = st.text_input("Login Key", type="password")
        if st.button("Login"):
            if pw == "ghs123": st.session_state.auth = True; st.rerun()
            else: st.error("Wrong Key")
        st.stop()
    if st.button("Logout"): st.session_state.clear(); st.rerun()

# --- MAIN APP ---
df = get_students(); fil = df[df["Class"] == cl] if not df.empty else pd.DataFrame()
t1, t2, t3 = st.tabs(["🖊️ Marks Entry", "📋 Student Directory", "🖨️ Print Results"])

with t1:
    if fil.empty: st.info(f"Class {cl} mein koi student nahi hai. Directory tab se add karein.")
    else:
        sn = st.selectbox("Select Student", fil["Name"].unique())
        sd = fil[fil["Name"] == sn].iloc[0].to_dict()
        with st.form("marks_form"):
            st.write(f"Marks entry for: **{sn}**")
            for s in sel:
                c1, c2 = st.columns(2)
                sd[s] = c1.number_input(f"{s} Obtained", 0, 500, int(sd.get(s, 0)))
                sd[f"Total_{s}"] = c2.number_input(f"{s} Total", 1, 500, int(sd.get(f"Total_{s}", 50)))
            if st.form_submit_button("Save Marks Permanently"):
                if save_student(sd): st.success("Cloud mein save ho gaya!"); st.rerun()

with t2:
    with st.expander(f"Add New Student to {cl}"):
        with st.form("add_form"):
            r, n, f = st.columns(3); rl = r.number_input("Roll No", 1); name = n.text_input("Full Name"); fat = f.text_input("Father Name")
            if st.form_submit_button("Register"):
                new_stu = {"Roll No": rl, "Name": name, "Father Name": fat, "Class": cl, "Section": "A", **{s: 0 for s in SUBJECTS}, **{f"Total_{s}": 50 for s in SUBJECTS}}
                if save_student(new_stu):
                    st.success("Registered!"); st.rerun()
    if not fil.empty:
        st.write("Existing Students:")
        for i, row in fil.sort_values("Roll No").iterrows():
            c1, c2 = st.columns([5, 1])
            c1.write(f"**Roll {row['Roll No']}**: {row['Name']}")
            if c2.button("🗑️ Delete", key=f"del_{cl}_{row['Roll No']}"):
                delete_student(cl, row['Roll No']); st.rerun()

with t3:
    if fil.empty: st.error("No students found in this class.")
    else:
        pn = st.selectbox("Select Student to Print", fil["Name"].unique())
        if st.button("Generate Card"):
            pdf = ResultPDF(); pdf.draw(fil[fil["Name"] == pn].iloc[0], sel, logo)
            st.download_button(f"Download {pn}.pdf", bytes(pdf.output()), f"{pn}.pdf", "application/pdf")
        if st.button("Generate Bulk Result (Whole Class)"):
            pdf = ResultPDF()
            for _, r in fil.sort_values("Roll No").iterrows(): pdf.draw(r, sel, logo)
            st.download_button("Download Bulk PDF", bytes(pdf.output()), f"Class_{cl}_Results.pdf", "application/pdf")
