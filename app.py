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
@st.cache_data(ttl=300)
def get_students_cached(_db_ref):
    if _db_ref:
        try:
            docs = list(_db_ref.collection(*COL_PATH).stream())
            if docs: return pd.DataFrame([doc.to_dict() for doc in docs])
        except Exception: pass
    return pd.DataFrame(columns=["Roll No", "Name", "Father Name", "Class", "Section"] + SUBJECTS)

def save_student(data):
    if db:
        try:
            uid = f"{data['Class']}_{data['Section']}_{data['Roll No']}".replace(" ", "_")
            db.collection(*COL_PATH).document(uid).set(data)
            st.cache_data.clear() 
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
        self.set_line_width(0.5); self.rect(5, 5, 200, 287); self.set_line_width(0.2); self.rect(7, 7, 196, 283)
        if logo:
            try: self.image(logo, 10, 10, 25)
            except: pass
        self.set_font("Helvetica", 'B', 14); self.cell(190, 7, "GOVT. HIGH SCHOOL BHUTTA MOHABBAT", ln=True, align='C')
        self.set_font("Helvetica", 'B', 10); self.cell(190, 8, "STUDENT REPORT CARD - Session 2025-2026", ln=True, align='C')
        self.ln(2)
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
        pos_txt = str(int(d.get('Position', 0))) if 1 <= d.get('Position', 0) <= 5 else "---"
        self.ln(5); self.set_font("Helvetica", 'B', 10); self.cell(190, 10, f"PERCENTAGE: {perc:.1f}% | POSITION: {pos_txt} | GRADE: {grade}", 0, 1, 'C')
        self.ln(10); self.set_font("Helvetica", 'B', 9); self.cell(95, 10, "_______________________", 0, 0, 'C'); self.cell(95, 10, "_______________________", 0, 1, 'C')
        self.cell(95, 5, "CLASS TEACHER", 0, 0, 'C'); self.cell(95, 5, "HEAD MASTER (SAFDAR JAVED)", 0, 1, 'C')

class GrandAwardListPDF(FPDF):
    def generate_grand_list(self, grand_data):
        self.add_page()
        self.set_font("Helvetica", 'B', 16); self.cell(190, 10, "GOVT. HIGH SCHOOL BHUTTA MOHABBAT", ln=True, align='C')
        self.set_font("Helvetica", 'B', 12); self.cell(190, 8, "GRAND TOPPERS LIST (TOP 5 EACH SECTION)", ln=True, align='C')
        self.ln(5)
        
        for entry in grand_data:
            if self.get_y() > 220: self.add_page()
            self.set_fill_color(230, 230, 230); self.set_font("Helvetica", 'B', 11)
            self.cell(190, 10, f" {entry['class']} - SECTION: {entry['section']} ", 1, 1, 'L', True)
            
            # Header with Father Name included
            self.set_fill_color(245, 245, 245); self.set_font("Helvetica", 'B', 8)
            self.cell(12, 10, "Pos", 1, 0, 'C', True); self.cell(15, 10, "Roll", 1, 0, 'C', True)
            self.cell(63, 10, "Student Name", 1, 0, 'C', True); self.cell(63, 10, "Father Name", 1, 0, 'C', True)
            self.cell(17, 10, "Marks", 1, 0, 'C', True); self.cell(20, 10, "%", 1, 1, 'C', True)
            
            self.set_font("Helvetica", '', 9)
            for r in entry['students']:
                self.cell(12, 8, str(r['DisplayPos']), 1, 0, 'C'); self.cell(15, 8, str(r['Roll No']), 1, 0, 'C')
                self.cell(63, 8, f" {str(r['Name']).upper()[:28]}", 1, 0, 'L')
                self.cell(63, 8, f" {str(r['Father Name']).upper()[:28]}", 1, 0, 'L')
                self.cell(17, 8, str(int(r['Total'])), 1, 0, 'C'); self.cell(20, 8, f"{r['Perc']:.1f}%", 1, 1, 'C')
            self.ln(5)

# --- SIDEBAR ---
with st.sidebar:
    st.header("Class Management")
    cl = st.selectbox("Select Class", CLASSES); sc = st.selectbox("Select Section", SECTIONS)
    if st.button("🔄 Force Refresh Data"): st.cache_data.clear(); st.rerun()
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
if not df.empty and "Class" in df.columns:
    fil = df[(df["Class"] == cl) & (df["Section"] == sc)].copy()
    if not fil.empty:
        fil[SUBJECTS] = fil[SUBJECTS].apply(pd.to_numeric, errors='coerce').fillna(0)
        fil['Total_Obtained'] = fil[sel].sum(axis=1)
        fil['Total_Possible'] = fil.apply(lambda r: sum([int(r.get(f"Total_{s}", 50)) for s in sel]), axis=1)
        fil['Position'] = fil['Total_Obtained'].rank(ascending=False, method='min').astype(int)
        fil = fil.sort_values("Roll No")
else: fil = pd.DataFrame(columns=["Roll No", "Name", "Father Name", "Class", "Section"] + SUBJECTS)

tab1, tab2, tab3 = st.tabs(["🖊️ Marks", "📋 Directory", "🖨️ Print"])

with tab1:
    if fil.empty: st.info("Class empty.")
    else:
        sn = st.selectbox("Select Student", fil["Name"].unique())
        s_row = fil[fil["Name"] == sn].iloc[0].to_dict()
        with st.form("marks_form"):
            for s in sel:
                c1, c2 = st.columns(2)
                s_row[s] = c1.number_input(f"{s} Obt", 0, 500, int(s_row.get(s, 0)))
                s_row[f"Total_{s}"] = c2.number_input(f"{s} Tot", 1, 500, int(s_row.get(f"Total_{s}", 50)))
            if st.form_submit_button("Save Marks"):
                if save_student(s_row): st.success("Saved!"); st.rerun()

with tab2:
    with st.expander("➕ Add Student"):
        with st.form("add_form"):
            r_c, n_c, f_c = st.columns(3); roll = r_c.number_input("Roll", 1); name = n_c.text_input("Name"); fat = f_c.text_input("Father")
            if st.form_submit_button("Add"):
                save_student({"Roll No": roll, "Name": name, "Father Name": fat, "Class": cl, "Section": sc, **{s: 0 for s in SUBJECTS}, **{f"Total_{s}": 50 for s in SUBJECTS}})
                st.rerun()
    for i, row in fil.iterrows():
        c1, c2, c3 = st.columns([4, 1, 1]); c1.write(f"Roll {row['Roll No']}: {row['Name']}")
        if c2.button("📝", key=f"ed_{row['Roll No']}"): st.session_state[f"ed_{row['Roll No']}"] = True
        if c3.button("🗑️", key=f"de_{row['Roll No']}"): delete_student(cl, sc, row['Roll No']); st.rerun()
        if st.session_state.get(f"ed_{row['Roll No']}", False):
            with st.form(f"fe_{row['Roll No']}"):
                un = st.text_input("Name", row['Name']); uf = st.text_input("Father", row['Father Name']); ur = st.number_input("Roll", value=int(row['Roll No']))
                if st.form_submit_button("Update"):
                    if ur != row['Roll No']: delete_student(cl, sc, row['Roll No'])
                    upd = row.to_dict(); upd.update({"Name": un, "Father Name": uf, "Roll No": ur})
                    save_student(upd); st.session_state[f"ed_{row['Roll No']}"] = False; st.rerun()

with tab3:
    if fil.empty: st.warning("No data.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            pn = st.selectbox("Print", fil["Name"].unique())
            if st.button("Single Card"):
                pdf = ResultPDF(); pdf.draw(fil[fil["Name"] == pn].iloc[0].to_dict(), sel, logo)
                st.download_button(f"DL_{pn}.pdf", bytes(pdf.output(dest='S').encode('latin-1')), f"{pn}.pdf", "application/pdf")
            if st.button("Bulk PDF"):
                pdf_b = ResultPDF()
                for _, r in fil.iterrows(): pdf_b.draw(r.to_dict(), sel, logo)
                st.download_button("Bulk.pdf", bytes(pdf_b.output(dest='S').encode('latin-1')), f"Bulk_{cl}_{sc}.pdf", "application/pdf")
        with c2:
            st.subheader("🏆 Grand Toppers List")
            if st.button("Generate GRAND TOPPERS"):
                grand_data = []
                for c_item in CLASSES:
                    for s_item in SECTIONS:
                        c_df = df[(df["Class"] == c_item) & (df["Section"] == s_item)].copy()
                        if not c_df.empty:
                            c_df[SUBJECTS] = c_df[SUBJECTS].apply(pd.to_numeric, errors='coerce').fillna(0)
                            # Only count subjects that have ANY marks in this class
                            active_subs = [s for s in SUBJECTS if c_df[s].sum() > 0]
                            if not active_subs: active_subs = ["English"]
                            
                            c_df['Total_Obtained'] = c_df[active_subs].sum(axis=1)
                            c_df['Max'] = c_df.apply(lambda r: sum([int(r.get(f"Total_{s}", 50)) for s in active_subs]), axis=1)
                            
                            top5 = c_df.sort_values("Total_Obtained", ascending=False).head(5)
                            students_list = []
                            for idx, r_t in enumerate(top5.to_dict('records')):
                                students_list.append({
                                    'DisplayPos': idx + 1, 'Roll No': r_t['Roll No'], 
                                    'Name': r_t['Name'], 'Father Name': r_t.get('Father Name', '---'),
                                    'Total': r_t['Total_Obtained'], 
                                    'Perc': (r_t['Total_Obtained'] / r_t['Max'] * 100) if r_t['Max'] > 0 else 0
                                })
                            grand_data.append({'class': c_item, 'section': s_item, 'students': students_list})
                
                if grand_data:
                    pdf_g = GrandAwardListPDF()
                    pdf_g.generate_grand_list(grand_data)
                    st.download_button("Download_Grand_Toppers.pdf", bytes(pdf_g.output(dest='S').encode('latin-1')), "Grand_Toppers.pdf", "application/pdf")
