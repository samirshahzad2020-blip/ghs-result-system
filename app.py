import streamlit as st
import pandas as pd
from fpdf import FPDF
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- APP CONFIG ---
st.set_page_config(page_title="GHS Result System", layout="wide", page_icon="🏫")

# --- FIREBASE SETUP ---
APP_ID = "ghs-bhutta-mohabbat-final"

def init_firebase():
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets and "textkey" in st.secrets["firebase"]:
                key_dict = json.loads(st.secrets["firebase"]["textkey"])
                creds = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(creds)
            else: return None
        except Exception: return None
    return firestore.client()

db = init_firebase()

# --- CONSTANTS ---
CLASSES = ["Nursery", "K.G", "1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"]
DEFAULT_SUBJECTS = ["English", "Urdu", "Mathematics", "Islamiat", "Science", "Social Study", "Computer", "Tajuma-tu-Quran"]

# --- DATA FUNCTIONS ---
def get_data():
    if db:
        try:
            docs = db.collection("artifacts", APP_ID, "public", "data", "students").stream()
            data = [doc.to_dict() for doc in docs]
            return pd.DataFrame(data) if data else pd.DataFrame(columns=["Roll No", "Name", "Class"])
        except: return st.session_state.get('local_db', pd.DataFrame(columns=["Roll No", "Name", "Class"]))
    else:
        if 'local_db' not in st.session_state: st.session_state.local_db = pd.DataFrame(columns=["Roll No", "Name", "Class"])
        return st.session_state.local_db

def save_data(student):
    if db:
        uid = f"{student['Class']}_{student['Roll No']}".replace(" ", "_")
        db.collection("artifacts", APP_ID, "public", "data", "students").document(uid).set(student)
    else:
        if 'local_db' not in st.session_state: st.session_state.local_db = pd.DataFrame([student])
        else:
            mask = (st.session_state.local_db['Roll No'] == student['Roll No']) & (st.session_state.local_db['Class'] == student['Class'])
            if mask.any():
                idx = st.session_state.local_db[mask].index[0]
                for k, v in student.items(): st.session_state.local_db.at[idx, k] = v
            else: st.session_state.local_db = pd.concat([st.session_state.local_db, pd.DataFrame([student])], ignore_index=True)

def delete_data(cls, roll):
    if db:
        uid = f"{cls}_{roll}".replace(" ", "_")
        db.collection("artifacts", APP_ID, "public", "data", "students").document(uid).delete()
    else:
        mask = (st.session_state.local_db['Roll No'] == roll) & (st.session_state.local_db['Class'] == cls)
        st.session_state.local_db = st.session_state.local_db[~mask].reset_index(drop=True)

# --- PDF GENERATOR ---
class ResultPDF(FPDF):
    def draw_card(self, data, subs, logo=None):
        self.add_page()
        self.set_line_width(0.5); self.rect(5, 5, 200, 287)
        self.set_line_width(0.2); self.rect(7, 7, 196, 283)
        if logo:
            try: self.image(logo, 10, 10, 25)
            except: pass
        self.set_font("Helvetica", 'B', 8); self.cell(190, 4, "SCHOOL EDUCATION DEPARTMENT", ln=True, align='C')
        self.set_font("Helvetica", 'B', 14); self.cell(190, 7, "GOVT. HIGH SCHOOL BHUTTA MOHABBAT", ln=True, align='C')
        self.set_font("Helvetica", 'B', 9); self.cell(190, 5, "EMIS CODE: 39310025 | DISTRICT OKARA", ln=True, align='C')
        self.ln(2); self.set_font("Helvetica", 'B', 18); self.set_text_color(70, 130, 180)
        self.cell(190, 10, "STUDENT REPORT CARD", ln=True, align='C')
        self.set_text_color(0, 0, 0); self.set_font("Helvetica", 'B', 10); self.cell(190, 8, "Session 2025-2026", ln=True, align='C')
        self.set_fill_color(200, 220, 240); self.set_font("Helvetica", 'B', 9)
        self.cell(95, 8, f" NAME: {str(data['Name']).upper()}", 1, 0, 'L', True)
        self.cell(95, 8, f" FATHER: {str(data['Father Name']).upper()}", 1, 1, 'L', True)
        self.cell(63, 8, f" CLASS: {data['Class']}", 1, 0, 'L', True); self.cell(64, 8, f" ROLL: {data['Roll No']}", 1, 0, 'L', True); self.cell(63, 8, f" SEC: {data.get('Section','A')}", 1, 1, 'L', True)
        self.ln(3); self.set_fill_color(50, 50, 50); self.set_text_color(255, 255, 255)
        self.cell(110, 9, "SUBJECT", 1, 0, 'C', True); self.cell(40, 9, "TOTAL", 1, 0, 'C', True); self.cell(40, 9, "OBTAINED", 1, 1, 'C', True)
        self.set_text_color(0, 0, 0); self.set_font("Helvetica", '', 10)
        go = 0; gm = 0
        for s in subs:
            o = int(data.get(s, 0)); t = int(data.get(f"Total_{s}", 50)); go += o; gm += t
            self.cell(110, 8, f" {s}", 1); self.cell(40, 8, str(t), 1, 0, 'C'); self.cell(40, 8, str(o), 1, 1, 'C')
        self.set_font("Helvetica", 'B', 10); self.cell(110, 9, " GRAND TOTAL", 1); self.cell(40, 9, str(gm), 1, 0, 'C'); self.cell(40, 9, str(go), 1, 1, 'C')
        self.ln(20); self.set_font("Helvetica", 'I', 10)
        self.multi_cell(190, 6, '"Education is the most powerful weapon which you can use to change the world."\n"The beautiful thing about learning is that no one can take it away from you."', align='C')
        self.ln(15); self.set_font("Helvetica", 'B', 9)
        self.cell(95, 10, "_______________________", 0, 0, 'C'); self.cell(95, 10, "_______________________", 0, 1, 'C')
        self.cell(95, 5, "CLASS TEACHER", 0, 0, 'C'); self.cell(95, 5, "SENIOR HEAD MASTER (SAFDAR JAVED)", 0, 1, 'C')
        self.ln(5); self.set_font("Helvetica", '', 8); self.cell(190, 10, "Result Date: 31-03-2026", 0, 0, 'R')

# --- INTERFACE ---
if db is None: st.warning("⚠️ Data is in 'Temporary Mode'. Fix Secrets to save forever.")
with st.sidebar:
    act_cl = st.selectbox("Working Class", CLASSES); st.divider()
    if st.button("Check All"):
        for s in DEFAULT_SUBJECTS: st.session_state[f"s_{s}"] = True
    if st.button("Uncheck All"):
        for s in DEFAULT_SUBJECTS: st.session_state[f"s_{s}"] = False
    sel_s = [s for s in DEFAULT_SUBJECTS if st.checkbox(s, value=st.session_state.get(f"s_{s}", True), key=f"s_{s}")]
    st.divider(); logo = st.file_uploader("Logo", type=['png', 'jpg'])
    if 'auth' not in st.session_state:
        pw = st.text_input("Access Key", type="password")
        if st.button("Login"):
            if pw == "ghs123": st.session_state.auth = True; st.rerun()
            else: st.error("Wrong Key")
        st.stop()
    if st.sidebar.button("Logout"): st.session_state.clear(); st.rerun()

st_df = get_data(); fil = st_df[st_df["Class"] == act_cl]
t1, t2, t3 = st.tabs(["🖊️ Marks", "📋 Directory", "🖨️ Print"])

with t1:
    if fil.empty: st.info("No students.")
    else:
        sn = st.selectbox("Student", fil["Name"].unique())
        sd = fil[fil["Name"] == sn].iloc[0].to_dict()
        with st.form("mf"):
            for s in sel_s:
                c1, c2 = st.columns(2)
                sd[s] = c1.number_input(f"{s} Obt", 0, 500, int(sd.get(s,0)))
                sd[f"Total_{s}"] = c2.number_input(f"{s} Tot", 1, 500, int(sd.get(f"Total_{s}",50)))
            if st.form_submit_button("Save"): save_data(sd); st.success("Saved!"); st.rerun()

with t2:
    with st.expander("➕ Add Student"):
        with st.form("as"):
            r, n, f = st.columns(3); rl = r.number_input("Roll", 1); nm = n.text_input("Name"); fat = f.text_input("Father Name")
            if st.form_submit_button("Add"):
                save_data({"Roll No": rl, "Name": nm, "Father Name": fat, "Class": act_cl, "Section": "A", **{s: 0 for s in DEFAULT_SUBJECTS}, **{f"Total_{s}": 50 for s in DEFAULT_SUBJECTS}})
                st.rerun()
    for i, row in fil.iterrows():
        c_i, c_d = st.columns([4, 1])
        c_i.write(f"**Roll {row['Roll No']}**: {row['Name']}")
        if c_d.button("🗑️", key=f"d_{i}"): delete_data(row['Class'], row['Roll No']); st.rerun()

with t3:
    if fil.empty: st.error("No data.")
    else:
        if st.button("Generate Bulk Result"):
            pdf = ResultPDF()
            for _, r in fil.sort_values("Roll No").iterrows(): pdf.draw_card(r, sel_s, logo)
            st.download_button("Download PDF", bytes(pdf.output()), "Results.pdf", "application/pdf")
