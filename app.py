import streamlit as st
import fitz  # PyMuPDF (پی ڈی ایف صاف کرنے کے لیے)
import sqlite3
import pandas as pd
from fpdf import FPDF
import io

# --- ڈیٹا بیس سیٹ اپ ---
def init_db():
    conn = sqlite3.connect('school_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students 
                 (id INTEGER PRIMARY KEY, name TEXT, class TEXT, 
                  total_marks INTEGER, total_obtained INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- اسکول کی معلومات (Fixed) ---
SCHOOL_NAME = "Government High School Bhutta Mohabbat"
EMIS_CODE = "39310025"
DISTRICT = "Okara"

# --- سائیڈ بار مینیو ---
st.sidebar.image("https://via.placeholder.com/150", caption="GHS Bhutta Mohabbat") # یہاں اپنا لوگو لگائیں
menu = st.sidebar.selectbox("آپشن منتخب کریں", 
    ["Result Card Generator", "PDF Paper Cleaner", "Top 5 Merit List"])

# --- 1. PDF Paper Cleaner ---
if menu == "PDF Paper Cleaner":
    st.header("📄 PDF Paper Cleaner")
    st.info("اس ٹول کے ذریعے آپ کسی بھی پیپر سے ہیڈر، فوٹر اور واٹر مارک مٹا سکتے ہیں۔")
    
    uploaded_file = st.file_uploader("پیپر اپ لوڈ کریں (PDF)", type="pdf")
    
    if uploaded_file:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        for page in doc:
            # ہیڈر اور فوٹر کو سفید پٹی سے چھپانا
            header = fitz.Rect(0, 0, page.rect.width, 65)
            footer = fitz.Rect(0, page.rect.height - 60, page.rect.width, page.rect.height)
            # واٹر مارک/مونوگرام کی جگہ (اوپر دائیں طرف)
            monogram = fitz.Rect(page.rect.width - 150, 0, page.rect.width, 50)
            
            for area in [header, footer, monogram]:
                page.draw_rect(area, color=(1, 1, 1), fill=(1, 1, 1))
        
        output = io.BytesIO()
        doc.save(output)
        st.success("ہیڈر اور فوٹر کامیابی سے ختم کر دیے گئے ہیں!")
        st.download_button("صاف شدہ پیپر ڈاؤن لوڈ کریں", output.getvalue(), "Cleaned_Paper.pdf")

# --- 2. Top 5 Merit List ---
elif menu == "Top 5 Merit List":
    st.header("🏆 Position Holders (Top 5)")
    
    conn = sqlite3.connect('school_data.db')
    query = """
        SELECT * FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY class ORDER BY total_obtained DESC) as rank
            FROM students
        ) WHERE rank <= 5
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        st.dataframe(df)
        
        # PDF بنانے کا لاجک
        if st.button("Download Award List PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, SCHOOL_NAME, ln=True, align='C')
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, f"District: {DISTRICT} | EMIS: {EMIS_CODE}", ln=True, align='C')
            pdf.ln(10)
            
            # Table Header
            pdf.set_fill_color(200, 220, 255)
            pdf.cell(15, 10, "Rank", 1, 0, 'C', True)
            pdf.cell(30, 10, "Class", 1, 0, 'C', True)
            pdf.cell(80, 10, "Student Name", 1, 0, 'C', True)
            pdf.cell(40, 10, "Obtained", 1, 1, 'C', True)
            
            for index, row in df.iterrows():
                pdf.cell(15, 10, str(row['rank']), 1)
                pdf.cell(30, 10, str(row['class']), 1)
                pdf.cell(80, 10, str(row['name']), 1)
                pdf.cell(40, 10, str(row['total_obtained']), 1, 1)
            
            st.download_button("ڈاؤن لوڈ کریں", pdf.output(dest='S').encode('latin-1'), "Award_List.pdf")
    else:
        st.warning("فی الحال ڈیٹا بیس میں کوئی ریکارڈ موجود نہیں ہے۔")

# --- 3. Result Card Generator (آپ کا پرانا کوڈ) ---
else:
    st.header("📋 Student Result Card Generator")
    # یہاں آپ کا پرانا فارم والا کوڈ (Name, Roll No, Marks) آ جائے گا
    st.write("اپنے طلباء کا ڈیٹا یہاں درج کریں اور رزلٹ کارڈ جنریٹ کریں۔")
    # مثال کے طور پر:
    name = st.text_input("طالب علم کا نام")
    cls = st.selectbox("کلاس", ["9th", "10th"])
    obt = st.number_input("حاصل کردہ نمبر", min_value=0)
    
    if st.button("Save & Generate"):
        # ڈیٹا بیس میں سیو کرنے کا لاجک
        conn = sqlite3.connect('school_data.db')
        c = conn.cursor()
        c.execute("INSERT INTO students (name, class, total_obtained) VALUES (?, ?, ?)", (name, cls, obt))
        conn.commit()
        conn.close()
        st.success(f"{name} کا ڈیٹا محفوظ کر لیا گیا ہے۔")
