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
@st.cache_data(ttl=600)
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

# --- PDF ENGINE ---
class ResultPDF(FPDF):
    def draw(self, d, subs, logo):
        self.add_page()
        self.set_line_width(0.5); self.rect(5, 5, 200, 287)
        self.set_line_width(0.2); self.rect(7, 7, 196, 283)
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
        
        # LOGIC: Only show position if it is between 1 and 5
        raw_pos = d.get('Position', 99)
        display_pos = str(raw_pos) if 1 <= int(raw_pos) <= 5 else "---"

        self.set_font("Helvetica", 'B', 8)
        self.cell(47, 10, f"PERC: {perc:.1f}%", 1, 0, 'C')
        self.cell(47, 10, f"POS: {display_pos}", 1, 0, 'C')
        self.cell(47, 10, f"PERF: {perf}", 1, 0, 'C')
        self.cell(49, 10, f"GRADE: {grade}", 1, 1, 'C')
        
        self.ln(15); self.set_font("Helvetica", 'I', 10); 
        self.multi_cell(190, 6, '"Education is the most powerful weapon which you can use to change the world."\n"The beautiful thing about learning is that no one can take it away from you."', align='C')
        self.ln(15); self.set_font("Helvetica", 'B', 9); self.cell(95, 10, "_______________________", 0, 0, 'C'); self.cell(95, 10, "_______________________", 0, 1, 'C')
        self.cell(95, 5, "CLASS TEACHER", 0, 0, 'C'); self.cell(95, 5, "SENIOR HEAD MASTER (SAFDAR JAVED)", 0, 1, 'C')
        self.ln(5); self.set_font("Helvetica", '', 8); self.cell(190, 10, "Result Date: 31-03-2026", 0, 0, 'R')

class AwardListPDF(FPDF):
    def generate(self, data_list, cl_name, sec_name):
        self.add_page()
        self.set_font("Helvetica", 'B', 14); self.cell(190, 10, "GOVT. HIGH SCHOOL BHUTTA MOHABBAT", ln=True, align='C')
        self.set_font("Helvetica", 'B', 12); self.cell(190, 8, f"AWARD LIST - {cl_name} ({sec_name})", ln=True, align='C')
        self.ln(5); self.set_fill_color(230, 230, 230); self.set_font("Helvetica", 'B', 10)
        self.cell(15, 10, "Pos", 1, 0, 'C', True); self.cell(20, 10, "Roll", 1, 0, 'C', True); self.cell(90, 10, "Student Name", 1, 0, 'C', True); self.cell(30, 10, "Marks", 1, 0, 'C', True); self.cell(35, 10, "%", 1, 1, 'C', True)
        self.set_font("Helvetica", '', 10)
        # Sorting data by marks for the award list
        sorted_list = sorted(data_list, key=lambda x: x['Total'], reverse=True)
        for i, r in enumerate(sorted_list):
            pos_text = str(i+1) if (i+1) <= 5 else "---"
            if (i+1) <= 5: self.set_font("Helvetica", 'B', 10); self.set_fill_color(245, 245, 220)
            else: self.set_font("Helvetica", '', 10); self.set_fill_color(255, 255, 255)
            
            self.cell(15, 8, pos_text, 1, 0, 'C', True)
            self.cell(20, 8, str(r['Roll No']), 1, 0, 'C', True)
            self.cell(90, 8, f" {str(r['Name']).upper()}", 1, 0, 'L', True)
            self.cell(30, 8, str(r['Total']), 1, 0, 'C', True)
            self.cell(35, 8, f"{r['Perc']:.1f}%", 1, 1, 'C', True)

# --- UI ---
with st.sidebar:
    st.header("Settings")
    cl = st.selectbox("Select Class", CLASSES)
    sc = st.selectbox("Select Section", SECTIONS)
    if st.button("🔄 Force Refresh"): st.cache_data.clear(); st.rerun()
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
        fil['Total_Obtained'] = fil[sel].apply(pd.to_numeric).sum(axis=1)
        fil['Position'] = fil['Total_Obtained'].rank(ascending=False, method='min').astype(int)
        fil = fil.sort_values("Roll No")
else:
    fil = pd.DataFrame(columns=["Roll No", "Name", "Father Name", "Class", "Section"] + SUBJECTS)

t1, t2, t3 = st.tabs(["🖊️ Marks Entry", "📋 Student Directory", "🖨️ Print Results"])

with t1:
    if fil.empty: st.info("No students found.")
    else:
        sn = st.selectbox("Select Student", fil["Name"].unique(), key="m_sel")
        s_row = fil[fil["Name"] == sn].iloc[0].to_dict()
        with st.form("marks_form"):
            for s in sel:
                c1, c2 = st.columns(2)
                s_row[s] = c1.number_input(f"{s} Obt", 0, 500, int(s_row.get(s, 0)))
                s_row[f"Total_{s}"] = c2.number_input(f"{s} Tot", 1, 500, int(s_row.get(f"Total_{s}", 50)))
            if st.form_submit_button("Save Marks"):
                if save_student(s_row): st.success("Saved!"); st.rerun()

with t2:
    with st.expander("➕ Add New Student"):
        with st.form("add_form"):
            r_i, n_i, f_i = st.columns(3)
            roll = r_i.number_input("Roll No", 1)
            name = n_i.text_input("Full Name")
            father = f_i.text_input("Father Name")
            if st.form_submit_button("Register"):
                new_s = {"Roll No": roll, "Name": name, "Father Name": father, "Class": cl, "Section": sc}
                for s in SUBJECTS: new_s[s] = 0; new_s[f"Total_{s}"] = 50
                if save_student(new_s): st.success("Added!"); st.rerun()
    
    st.write("### Current Students")
    for i, row in fil.iterrows():
        with st.container():
            c1, c2, c3 = st.columns([4, 1, 1])
            c1.write(f"**Roll {row['Roll No']}**: {row['Name']}")
            
            # EDIT Button
            if c2.button("📝", key=f"edit_btn_{row['Roll No']}"):
                st.session_state[f"editing_{row['Roll No']}"] = True
            
            # DELETE Button
            if c3.button("🗑️", key=f"del_{row['Roll No']}"):
                delete_student(cl, sc, row['Roll No']); st.rerun()
            
            # SHOW EDIT FORM IF CLICKED
            if st.session_state.get(f"editing_{row['Roll No']}", False):
                with st.form(f"edit_form_{row['Roll No']}"):
                    new_n = st.text_input("Edit Name", row['Name'])
                    new_f = st.text_input("Edit Father Name", row['Father Name'])
                    new_r = st.number_input("Edit Roll No", value=int(row['Roll No']))
                    if st.form_submit_button("Update Profile"):
                        # Delete old entry (if roll no changed) and save new
                        if new_r != row['Roll No']: delete_student(cl, sc, row['Roll No'])
                        updated_data = row.to_dict()
                        updated_data.update({"Name": new_n, "Father Name": new_f, "Roll No": new_r})
                        save_student(updated_data)
                        st.session_state[f"editing_{row['Roll No']}"] = False
                        st.rerun()

with tab3:
    if fil.empty: st.warning("No data.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            pn = st.selectbox("Select Student", fil["Name"].unique(), key="p_sel")
            if st.button("Generate Card"):
                pdf = ResultPDF(); pdf.draw(fil[fil["Name"] == pn].iloc[0].to_dict(), sel, logo)
                st.download_button(f"Download_{pn}.pdf", bytes(pdf.output()), f"{pn}.pdf")

        with c2:
            if st.button("Generate All Result Cards"):
                pdf_bulk = ResultPDF()
                for _, r in fil.iterrows(): pdf_bulk.draw(r.to_dict(), sel, logo)
                st.download_button("Download Bulk.pdf", bytes(pdf_bulk.output()), f"Bulk_{cl}_{sc}.pdf")
            
            st.divider()
            if st.button("Generate Award List"):
                aw_data = []
                for _, r in fil.iterrows():
                    obt = sum([int(r.get(s, 0)) for s in sel])
                    tot = sum([int(r.get(f"Total_{s}", 50)) for s in sel])
                    aw_data.append({"Roll No": r['Roll No'], "Name": r['Name'], "Total": obt, "Perc": (obt/tot*100) if tot>0 else 0})
                pdf_aw = AwardListPDF(); pdf_aw.generate(aw_data, cl, sc)
                st.download_button("Download Award List.pdf", bytes(pdf_aw.output()), f"AwardList_{cl}_{sc}.pdf")
