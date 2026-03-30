import streamlit as st
import fitz  # PyMuPDF
import sqlite3
import pandas as pd
from fpdf import FPDF
import io

# --- اسکول کی معلومات (Fixed) ---
SCHOOL_NAME = "Government High School Bhutta Mohabbat"
EMIS_CODE = "39310025"
DISTRICT = "Okara"

# --- ڈیٹا بیس فنکشنز ---
def init_db():
    conn = sqlite3.connect('ghs_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, roll_no TEXT, 
                  class TEXT, total_marks INTEGER, obtained_marks INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- مین ایپ انٹرفیس ---
st.set_page_config(page_title="GHS Bhutta Mohabbat Portal", layout="wide")
st.sidebar.title("GHS Management System")
menu = st.sidebar.radio("کون سا کام کرنا ہے؟", 
    ["Result Card Generator", "PDF Paper Cleaner", "Top 5 Position Holders"])

# --- 1. PDF Paper Cleaner (With Advanced Watermark Remover) ---
if menu == "PDF Paper Cleaner":
    st.header("📄 PDF Paper Cleaner & Watermark Remover")
    st.write("یہ ٹول پیپر کے ہیڈر، فوٹر اور درمیان سے ویب سائٹ کا نام (Watermark) صاف کر دے گا۔")
    
    uploaded_file = st.file_uploader("پی ڈی ایف فائل یہاں اپ لوڈ کریں", type="pdf")
    
    if uploaded_file:
        # پی ڈی ایف کھولنا
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        
        # واٹر مارک کے ممکنہ الفاظ جو مٹانے ہیں
        targets = ["www.zahidnotes.com", "zahidnotes.com", "zahidnotes"]

        for page in doc:
            # 1. ہیڈر اور فوٹر کو مٹانا (سفید پٹی)
            header_rect = fitz.Rect(0, 0, page.rect.width, 75) # اوپر سے 75 پوائنٹس
            footer_rect = fitz.Rect(0, page.rect.height - 65, page.rect.width, page.rect.height) # نیچے سے 65
            
            page.draw_rect(header_rect, color=(1, 1, 1), fill=(1, 1, 1))
            page.draw_rect(footer_rect, color=(1, 1, 1), fill=(1, 1, 1))

            # 2. واٹر مارک (Text) ڈھونڈ کر مٹانا
            for target in targets:
                text_instances = page.search_for(target)
                for inst in text_instances:
                    # اس مخصوص جگہ کو سفید کر دو
                    page.draw_rect(inst, color=(1, 1, 1), fill=(1, 1, 1))

        # فائل سیو کرنا
        output_pdf = io.BytesIO()
        doc.save(output_pdf)
        
        st.success("پیپر بالکل صاف ہو گیا ہے!")
        st.download_button("صاف شدہ PDF ڈاؤن لوڈ کریں", 
                           data=output_pdf.getvalue(), 
                           file_name="GHS_Cleaned_Paper.pdf", 
                           mime="application/pdf")

# --- 2. Top 5 Position Holders (Automatic Award List) ---
elif menu == "Top 5 Position Holders":
    st.header("🏆 Class-wise Top 5 Merit List")
    
    conn = sqlite3.connect('ghs_data.db')
    # ہر کلاس کے ٹاپ 5 نکالنے کا SQL فارمولا
    query = """
        SELECT * FROM (
            SELECT name, roll_no, class, total_marks, obtained_marks,
            RANK() OVER (PARTITION BY class ORDER BY obtained_marks DESC) as position
            FROM students
        ) WHERE position <= 5
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        if st.button("Generate Combined Award List PDF"):
            pdf = FPDF()
            pdf.add_page()
            
            # اسکول ہیڈر
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, SCHOOL_NAME, ln=True, align='C')
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 8, f"EMIS: {EMIS_CODE} | District: {DISTRICT}", ln=True, align='C')
            pdf.cell(0, 8, "Official Top 5 Merit List", ln=True, align='C')
            pdf.ln(10)
            
            # ٹیبل ہیڈر
            pdf.set_fill_color(230, 230, 230)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(20, 10, "Pos", 1, 0, 'C', True)
            pdf.cell(30, 10, "Class", 1, 0, 'C', True)
            pdf.cell(80, 10, "Student Name", 1, 0, 'C', True)
            pdf.cell(30, 10, "Marks", 1, 0, 'C', True)
            pdf.cell(30, 10, "Percentage", 1, 1, 'C', True)

            # ڈیٹا بھرنا
            pdf.set_font("Arial", '', 11)
            for _, row in df.iterrows():
                perc = (row['obtained_marks'] / row['total_marks']) * 100
                pdf.cell(20, 10, str(int(row['position'])), 1, 0, 'C')
                pdf.cell(30, 10, row['class'], 1, 0, 'C')
                pdf.cell(80, 10, row['name'], 1, 0, 'L')
                pdf.cell(30, 10, str(row['obtained_marks']), 1, 0, 'C')
                pdf.cell(30, 10, f"{perc:.1f}%", 1, 1, 'C')

            st.download_button("Download Full List PDF", 
                               pdf.output(dest='S').encode('latin-1'), 
                               "GHS_Position_Holders.pdf")
    else:
        st.warning("ڈیٹا بیس میں ابھی کوئی ڈیٹا موجود نہیں ہے۔")

# --- 3. Result Card Generator (Form) ---
else:
    st.header("📝 Student Data Entry")
    with st.form("student_form"):
        col1, col2 = st.columns(2)
        name = col1.text_input("طالب علم کا نام")
        roll = col2.text_input("رول نمبر")
        cls = st.selectbox("کلاس منتخب کریں", ["6th", "7th", "8th", "9th", "10th"])
        total = st.number_input("کل نمبر", value=1100)
        obt = st.number_input("حاصل کردہ نمبر", value=0)
        
        submit = st.form_submit_button("ڈیٹا محفوظ کریں")
        
        if submit:
            conn = sqlite3.connect('ghs_data.db')
            c = conn.cursor()
            c.execute("INSERT INTO students (name, roll_no, class, total_marks, obtained_marks) VALUES (?,?,?,?,?)",
                      (name, roll, cls, total, obt))
            conn.commit()
            conn.close()
            st.success(f"{name} کا ڈیٹا محفوظ ہو گیا ہے۔ اب آپ 'Top 5' مینیو میں جا کر لسٹ دیکھ سکتے ہیں۔")
