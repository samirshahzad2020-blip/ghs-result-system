import streamlit as st
import pandas as pd
import datetime

# --- ERROR HANDLING FOR LIBRARIES ---
try:
    from fpdf import FPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

st.set_page_config(page_title="GHS Result System", layout="wide")

# --- DATA INITIALIZATION ---
if 'students_db' not in st.session_state:
    st.session_state.students_db = pd.DataFrame([
        {"ID": "S101", "Name": "Alice Smith", "Class": "10", "Math": 85, "English": 70},
        {"ID": "S102", "Name": "Bob Jones", "Class": "10", "Math": 45, "English": 55}
    ])

# --- LOGIN ---
if 'logged_in' not in st.session_state:
    st.title("🏫 GHS Management Portal")
    pwd = st.text_input("Access Key", type="password")
    if st.button("Login"):
        if pwd == "admin123":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Incorrect Key")
    st.stop()

# --- MAIN APP ---
st.title("Student Management Dashboard")

# Check if library is working
if not PDF_SUPPORT:
    st.warning("⚠️ PDF Library (fpdf2) is not installed yet. You can still manage marks, but PDF download is disabled.")

# Marks Management
st.subheader("📝 Marks Entry")
df = st.session_state.students_db.copy()
updated_df = st.data_editor(df, use_container_width=True, key="main_editor")

if st.button("Save Marks"):
    st.session_state.students_db = updated_df
    st.success("Marks saved successfully!")

# Result Generation
st.divider()
st.subheader("🖨️ Generate Result Card")
selected = st.selectbox("Select Student", st.session_state.students_db["Name"])

if st.button("Generate Result"):
    if not PDF_SUPPORT:
        st.error("Cannot generate PDF. Check requirements.txt")
    else:
        row = st.session_state.students_db[st.session_state.students_db["Name"] == selected].iloc[0]
        
        # PDF Creation
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="GHS ACADEMY - OFFICIAL RESULT", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.cell(100, 10, txt=f"Name: {row['Name']}", ln=True)
        pdf.cell(100, 10, txt=f"ID: {row['ID']}", ln=True)
        pdf.ln(5)
        pdf.cell(100, 10, txt=f"Math: {row['Math']}", ln=True)
        pdf.cell(100, 10, txt=f"English: {row['English']}", ln=True)
        
        pdf_output = pdf.output()
        st.download_button(
            label="⬇️ Download PDF Result",
            data=pdf_output,
            file_name=f"Result_{selected}.pdf",
            mime="application/pdf"
        )
