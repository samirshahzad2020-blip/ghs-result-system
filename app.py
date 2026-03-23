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

# --- DATA FUNCTIONS ---
def get_students():
    if db:
        try:
            docs = list(db.collection(*COL_PATH).stream())
            if docs:
                return pd.DataFrame([doc.to_dict() for doc in docs])
            else:
                return pd.DataFrame(columns=["Roll No", "Name", "Father Name", "Class", "Section"] + SUBJECTS)
        except Exception as e:
            if "429" in str(e):
                st.error("Google Database ki aaj ki limit (Quota) khatam ho gayi hai. Kal dobara chalay ga.")
            else:
                st.error(f"Data load nahi ho raha: {e}")
            return pd.DataFrame(columns=["Roll No", "Name", "Father Name", "Class", "Section"] + SUBJECTS)
    return st.session_state.get('local_db', pd.DataFrame(columns=["Roll No", "Name", "Father Name", "Class", "Section"] + SUBJECTS))

def save_student(data):
    if db:
        try:
            uid = f"{data['Class']}_{data['Section']}_{data['Roll No']}".replace(" ", "_")
            db.collection(*COL_PATH).document(uid).set(data)
            return True
        except Exception as e:
            st.error(f"Save nahi ho saka (Quota exceeded or Error): {e}")
            return False
    return False

def delete_student(cls, sec, roll):
    if db:
        try:
            uid = f"{cls}_{sec}_{roll}".replace(" ", "_")
            db.collection(*COL_PATH).document(uid).delete()
        except: pass

# --- PDF ENGINES ---
class ResultPDF(FPDF):
    def draw(self, d, subs, logo):
        self.add_page()
        self.set_line_width(0.5); self.rect(5, 5, 200, 287); self.set_line_width(0.2); self.rect(7, 7, 196, 283)
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

class AwardListPDF(FPDF):
    def generate(self, data_list, cl_name, sec_name):
        self.add_page()
        self.set_font("Helvetica", 'B', 14); self.cell(190, 10, "AWARD LIST - " + cl_name, ln=True, align='C')
        self.ln(5); self.set_font("Helvetica", 'B', 10)
        self.cell(20, 10, "Roll", 1); self.cell(100, 10, "Name", 1); self.cell(35, 10, "Marks", 1); self.cell(35, 10, "%", 1, 1)
        self.set_font("Helvetica", '', 10)
        for r in data_list:
            self.cell(20, 8, str(r['Roll No']), 1); self.cell(100, 8, str(r['Name']), 1); self.cell(35, 8, str(r['Total']), 1); self.cell(35, 8, f"{r['Perc']:.1f}%", 1, 1)

# --- UI ---
with st.sidebar:
    st.header("Settings")
    cl = st.selectbox("Class", CLASSES)
    sc = st.selectbox("Section", SECTIONS)
    sel = [s for s in SUBJECTS if st.checkbox(s, value=True, key=f"s_{s}")]
    logo = st.file_uploader("Logo", type=['png', 'jpg'])
    if 'auth' not in st.session_state:
        pw = st.text_input("Key", type="password")
        if st.button("Login"):
            if pw == "ghs123": st.session_state.auth = True; st.rerun()
        st.stop()

# --- MAIN ---
df = get_students()
fil = df[(df["Class"] == cl) & (df["Section"] == sc)] if not df.empty else pd.DataFrame()

t1, t2, t3 = st.tabs(["🖊️ Marks", "📋 Directory", "🖨️ Print"])

with t1:
    if fil.empty: st.info("No students.")
    else:
        sn = st.selectbox("Student", fil["Name"].unique())
        s_row = fil[fil["Name"] == sn].iloc[0].to_dict()
        with st.form("m_form"):
            for s in sel:
                c1, c2 = st.columns(2)
                s_row[s] = c1.number_input(f"{s}", 0, 500, int(s_row.get(s, 0)))
                s_row[f"Total_{s}"] = c2.number_input(f"Total {s}", 1, 500, int(s_row.get(f"Total_{s}", 50)))
            if st.form_submit_button("Save"):
                if save_student(s_row): st.success("Saved!"); st.rerun()

with t2:
    with st.form("a_form"):
        r_i = st.number_input("Roll No", 1)
        n_i = st.text_input("Name")
        f_i = st.text_input("Father Name")
        if st.form_submit_button("Add Student"):
            new_data = {"Roll No": r_i, "Name": n_i, "Father Name": f_i, "Class": cl, "Section": sc}
            for s in SUBJECTS: new_data[s] = 0; new_data[f"Total_{s}"] = 50
            if save_student(new_data): st.success("Added!"); st.rerun()
    
    if not fil.empty:
        for i, row in fil.sort_values("Roll No").iterrows():
            c1, c2 = st.columns([5,1])
            c1.write(f"Roll {row['Roll No']}: {row['Name']}")
            if c2.button("🗑️", key=f"d_{row['Roll No']}"):
                delete_student(cl, sc, row['Roll No']); st.rerun()

with t3:
    if fil.empty: st.warning("No data.")
    else:
        pn = st.selectbox("Print", fil["Name"].unique(), key="p_sel")
        if st.button("Result Card"):
            pdf = ResultPDF(); pdf.draw(fil[fil["Name"] == pn].iloc[0], sel, logo)
            st.download_button(f"Download_{pn}.pdf", bytes(pdf.output()), f"{pn}.pdf")
        
        st.divider()
        if st.button("Award List"):
            aw_data = []
            for _, r in fil.sort_values("Roll No").iterrows():
                obt = sum([int(r.get(s, 0)) for s in sel])
                tot = sum([int(r.get(f"Total_{s}", 50)) for s in sel])
                aw_data.append({"Roll No": r['Roll No'], "Name": r['Name'], "Total": obt, "Perc": (obt/tot*100) if tot>0 else 0})
            pdf_aw = AwardListPDF(); pdf_aw.generate(aw_data, cl, sc)
            st.download_button("Download Award List.pdf", bytes(pdf_aw.output()), "AwardList.pdf")
