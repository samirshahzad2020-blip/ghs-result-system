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
COL_PATH = ["artifacts", "ghs-bhutta-mohabbat-v10", "public", "data", "students"]

# --- CONSTANTS ---
CLASSES = ["Nursery", "K.G", "1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"]
SECTIONS = ["A", "B"]
SUBJECTS = ["English", "Urdu", "Mathematics", "Islamiat", "Science", "Social Study", "Computer", "Tajuma-tu-Quran"]

def get_grade_perf(p):
    if p >= 80: return "A+", "Excellent"
    elif p >= 70: return "A", "Very Good"
    elif p >= 60: return "B", "Good"
    elif p >= 50: return "C", "Satisfactory"
    elif p >= 40: return "D", "Fair"
    else: return "F", "Poor / Fail"

# --- DATA FUNCTIONS (WITH SAFETY) ---
@st.cache_data(ttl=300) # 5 Minute Cache
def get_students_cached(_db_ref):
    if _db_ref:
        try:
            docs = list(_db_ref.collection(*COL_PATH).stream())
            if docs:
                return pd.DataFrame([doc.to_dict() for doc in docs])
        except Exception as e:
            st.warning(f"Database sync issue: {e}")
    # Return empty DF with required columns to prevent KeyError
    return pd.DataFrame(columns=["Roll No", "Name", "Father Name", "Class", "Section"] + SUBJECTS)

def save_student(data):
    if db:
        try:
            uid = f"{data['Class']}_{data['Section']}_{data['Roll No']}".replace(" ", "_")
            db.collection(*COL_PATH).document(uid).set(data)
            st.cache_data.clear() # Clear cache on save
            return True
        except: return False
    return False

def delete_student(cls, sec, roll):
    if db:
        try:
            uid = f"{cls}_{sec}_{roll}".replace(" ", "_")
            db.collection(*COL_PATH).document(uid).delete()
            st.cache_data.clear()
        except: pass

# --- PDF ENGINES ---
class ResultPDF(FPDF):
    def draw(self, d, subs, logo):
        self.add_page()
        self.set_line_width(0.5); self.rect(5, 5, 200, 287)
        if logo:
            try: self.image(logo, 10, 10, 25)
            except: pass
        self.set_font("Helvetica", 'B', 14); self.cell(190, 7, "GOVT. HIGH SCHOOL BHUTTA MOHABBAT", ln=True, align='C')
        self.ln(5)
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
        perc = (obt_t / max_t * 100) if max_t > 0 else 0
        grade, perf = get_grade_perf(perc)
        self.ln(10); self.cell(190, 10, f"GRADE: {grade} | PERFORMANCE: {perf}", 0, 1, 'C')

# --- UI INTERFACE ---
with st.sidebar:
    st.header("Settings")
    cl = st.selectbox("Select Class", CLASSES)
    sc = st.selectbox("Select Section", SECTIONS)
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    sel = [s for s in SUBJECTS if st.checkbox(s, value=True, key=f"s_{s}")]
    logo = st.file_uploader("Upload Logo", type=['png', 'jpg'])
    if 'auth' not in st.session_state:
        pw = st.text_input("Key", type="password")
        if st.button("Login"):
            if pw == "ghs123": st.session_state.auth = True; st.rerun()
        st.stop()

# --- MAIN ---
df = get_students_cached(db)

# Safety check for filter
if not df.empty and "Class" in df.columns:
    fil = df[(df["Class"] == cl) & (df["Section"] == sc)]
else:
    fil = pd.DataFrame(columns=["Roll No", "Name", "Father Name", "Class", "Section"] + SUBJECTS)

tab1, tab2, tab3 = st.tabs(["🖊️ Marks", "📋 Directory", "🖨️ Print"])

with tab1:
    if fil.empty: st.info("No students in this class/section.")
    else:
        sn = st.selectbox("Select Student", fil["Name"].unique())
        s_row = fil[fil["Name"] == sn].iloc[0].to_dict()
        with st.form("m_form"):
            for s in sel:
                c1, c2 = st.columns(2)
                s_row[s] = c1.number_input(f"{s} Obt", 0, 500, int(s_row.get(s, 0)))
                s_row[f"Total_{s}"] = c2.number_input(f"{s} Tot", 1, 500, int(s_row.get(f"Total_{s}", 50)))
            if st.form_submit_button("Save Marks"):
                if save_student(s_row): st.success("Saved!"); st.rerun()

with tab2:
    with st.form("a_form"):
        st.subheader("Add New Student")
        r_i = st.number_input("Roll No", 1)
        n_i = st.text_input("Name")
        f_i = st.text_input("Father Name")
        if st.form_submit_button("Register"):
            new_s = {"Roll No": r_i, "Name": n_i, "Father Name": f_i, "Class": cl, "Section": sc}
            for s in SUBJECTS: new_s[s] = 0; new_s[f"Total_{s}"] = 50
            if save_student(new_s): st.success("Added!"); st.rerun()
    
    if not fil.empty:
        st.write("### Student List")
        # Added safety for sort
        sorted_fil = fil.sort_values("Roll No") if "Roll No" in fil.columns else fil
        for i, row in sorted_fil.iterrows():
            c1, c2 = st.columns([5,1])
            c1.write(f"Roll {row['Roll No']}: {row['Name']}")
            if c2.button("🗑️", key=f"del_{row['Roll No']}"):
                delete_student(cl, sc, row['Roll No']); st.rerun()

with tab3:
    if fil.empty: st.warning("No data.")
    else:
        pn = st.selectbox("Select Student", fil["Name"].unique(), key="print_sel")
        if st.button("Generate Card"):
            pdf = ResultPDF(); pdf.draw(fil[fil["Name"] == pn].iloc[0], sel, logo)
            st.download_button(f"Download_{pn}.pdf", bytes(pdf.output()), f"{pn}.pdf")
