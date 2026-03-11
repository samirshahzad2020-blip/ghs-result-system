# app.py
import streamlit as st
import sqlite3
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
import io
import datetime

st.set_page_config(page_title="GHS Bhutta Mohabbat Result System", layout="wide")

# --- Database ---
conn = sqlite3.connect("students.db", check_same_thread=False)
c = conn.cursor()

# Tables
c.execute('''CREATE TABLE IF NOT EXISTS students
             (roll INTEGER PRIMARY KEY, name TEXT, father TEXT, class TEXT, section TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS marks
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              roll INTEGER, subject TEXT, total INTEGER, obtained INTEGER, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS teachers
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT UNIQUE, assigned_class TEXT)''')
conn.commit()

# --- Helper Functions ---
def get_grade_info(percentage):
    if percentage >= 80: return "A+", "Excellent"
    elif percentage >= 70: return "A", "Very Good"
    elif percentage >= 60: return "B", "Good"
    elif percentage >= 50: return "C", "Satisfactory"
    elif percentage >= 40: return "D", "Fair"
    else: return "F", "Poor"

def generate_pdf(data):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    # Borders
    p.setStrokeColor(colors.HexColor("#7B96AC"))
    p.setLineWidth(2)
    p.rect(15, 15, width - 30, height - 30)
    p.setLineWidth(1)
    p.rect(20, 20, width - 40, height - 40)
    # Header
    p.setFont("Helvetica", 9)
    p.drawCentredString(width / 2 + 30, height - 45, "SCHOOL EDUCATION DEPARTMENT")
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2 + 30, height - 62, data['school_name'].upper())
    p.setFont("Helvetica-Bold", 9)
    p.drawCentredString(width / 2 + 30, height - 75, f"EMIS CODE: {data['emis']} | DISTRICT {data['district'].upper()}")
    p.setFont("Helvetica-Bold", 20)
    p.setFillColor(colors.HexColor("#7B96AC"))
    p.drawCentredString(width / 2, height - 115, "STUDENT REPORT CARD")
    # Logo
    if data.get('logo'):
        try:
            logo_reader = ImageReader(data['logo'])
            p.drawImage(logo_reader, 45, height - 105, width=65, height=65, mask='auto')
        except: pass
    # Session
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(40, height - 130, f"Session {data['session']}")
    # Student Info
    info_data = [
        [f"NAME: {data['student_name'].upper()}", f"FATHER NAME: {data['father_name'].upper()}"],
        [f"CLASS: {data['class']}", f"ROLL NO: {data['roll']}", f"SECTION: {data['section']}"]
    ]
    t1 = Table(info_data[:1], colWidths=[275, 240])
    t1.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#7B96AC")),
                            ('TEXTCOLOR',(0,0),(-1,-1),colors.white),
                            ('FONTNAME',(0,0),(-1,-1),'Helvetica-Bold'),
                            ('FONTSIZE',(0,0),(-1,-1),9),
                            ('GRID',(0,0),(-1,-1),0.5,colors.white),
                            ('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    t2 = Table(info_data[1:], colWidths=[175,175,165])
    t2.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor("#7B96AC")),
                            ('TEXTCOLOR',(0,0),(-1,-1),colors.white),
                            ('FONTNAME',(0,0),(-1,-1),'Helvetica-Bold'),
                            ('FONTSIZE',(0,0),(-1,-1),9),
                            ('GRID',(0,0),(-1,-1),0.5,colors.white),
                            ('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    t1.wrapOn(p,40,height-160); t1.drawOn(p,40,height-160)
    t2.wrapOn(p,40,height-180); t2.drawOn(p,40,height-180)
    # Marks Table
    y_table = height-215
    p.setFillColor(colors.HexColor("#333333"))
    p.rect(40,y_table,515,25,fill=1)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold",10)
    p.drawString(150,y_table+8,"SUBJECT")
    p.drawString(350,y_table+8,"TOTAL MARKS")
    p.drawString(460,y_table+8,"OBTAINED")
    y_row = y_table-22
    p.setFillColor(colors.black)
    p.setFont("Helvetica",10)
    grand_total_max,grand_total_obt=0,0
    for sub,info in data['marks_data'].items():
        p.rect(40,y_row,515,22)
        p.line(330,y_row,330,y_row+22); p.line(440,y_row,440,y_row+22)
        p.drawString(45,y_row+7,sub)
        p.drawCentredString(385,y_row+7,str(info['total']))
        p.drawCentredString(495,y_row+7,str(info['obt']))
        grand_total_max+=info['total']; grand_total_obt+=info['obt']
        y_row-=22
    # Grand Total
    p.setFont("Helvetica-Bold",10)
    p.rect(40,y_row,515,22)
    p.drawString(45,y_row+7,"GRAND TOTAL")
    p.drawCentredString(385,y_row+7,str(grand_total_max))
    p.drawCentredString(495,y_row+7,str(grand_total_obt))
    # Result Summary
    y_summary = y_row-40
    perc = (grand_total_obt/grand_total_max*100) if grand_total_max>0 else 0
    grade,perf = get_grade_info(perc)
    box_w = 515/4
    for i,label in enumerate(["PERCENTAGE","POSITION","PERFORMANCE","FINAL GRADE"]):
        val=[f"{perc:.1f}%",data['position'],data.get("performance",perf),grade][i]
        p.rect(40+(i*box_w),y_summary,box_w,30)
        p.setFont("Helvetica-Bold",8)
        p.drawCentredString(40+(i*box_w)+(box_w/2),y_summary+18,f"{label}: {val}")
    p.showPage(); p.save()
    buffer.seek(0)
    return buffer

def generate_class_pdf_with_chart(summary, class_name):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2, height-50, f"Class Summary: {class_name}")
    # Table data
    data = [["Roll", "Name", "Total Marks", "Obtained", "Percentage", "Grade"]]
    percentages = []
    names = []
    for s in summary:
        data.append([s["Roll"], s["Name"], s["Total Marks"], s["Obtained"], s["Percentage"], s["Grade"]])
        percentages.append(float(s["Percentage"][:-1]))
        names.append(s["Name"])
    table = Table(data, colWidths=[50,150,80,80,80,80])
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#7B96AC")),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('GRID',(0,0),(-1,-1),0.5,colors.black)
    ]))
    table.wrapOn(p, 40, height-100)
    table.drawOn(p, 40, height - 100 - 22*len(data))
    # Bar chart
    drawing = Drawing(500, 200)
    bc = VerticalBarChart()
    bc.x = 50; bc.y = 20; bc.height = 150; bc.width = 400
    bc.data = [percentages]
    bc.categoryAxis.categoryNames = names
    bc.barWidth = 10; bc.groupSpacing = 10
    bc.valueAxis.valueMin = 0; bc.valueAxis.valueMax = 100; bc.valueAxis.valueStep = 10
    drawing.add(bc)
    renderPDF.draw(drawing, p, 40, 50)
    # Stats
    avg_perc = sum(percentages)/len(percentages)
    top_student = max(summary, key=lambda x: float(x["Percentage"][:-1]))
    pass_count = sum(1 for p in percentages if p>=40)
    fail_count = len(percentages) - pass_count
    stats_text = f"Class Average: {avg_perc:.1f}%  |  Topper: {top_student['Name']} ({top_student['Percentage']})  |  Pass: {pass_count}, Fail: {fail_count}"
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, 30, stats_text)
    p.showPage(); p.save(); buffer.seek(0)
    return buffer

# --- UI ---
st.title("GHS Bhutta Mohabbat Result System")
logo = st.file_uploader("Upload Logo (used in PDFs)", type=["jpg","png","jpeg"])
subs=["English","Urdu","Mathematics","Islamiat","Science","Social Study","Computer","Tarjuma-tu-Quran"]
st.info("Enter student marks and generate report cards without login.")

# --- Student Entry Form ---
with st.form("student_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Student Name")
        father = st.text_input("Father Name")
        roll = st.number_input("Roll No", min_value=1, step=1)
    with col2:
        class_name = st.text_input("Class")
        section = st.text_input("Section")
        session = st.text_input("Session (e.g., 2025-26)")
        position = st.text_input("Position (optional)")
    st.subheader("Enter Marks")
    marks_data = {}
    for sub in subs:
        col1, col2 = st.columns(2)
        with col1:
            total = st.number_input(f"Total Marks ({sub})", min_value=0, value=100)
        with col2:
            obt = st.number_input(f"Obtained Marks ({sub})", min_value=0, value=0)
        marks_data[sub] = {"total": total, "obt": obt}
    submit = st.form_submit_button("Save & Generate PDF")
    if submit:
        c.execute("INSERT OR REPLACE INTO students (roll, name, father, class, section) VALUES (?,?,?,?,?)",
                  (roll, name, father, class_name, section))
        for sub, info in marks_data.items():
            c.execute("INSERT INTO marks (roll, subject, total, obtained, date) VALUES (?,?,?,?,?)",
                      (roll, sub, info['total'], info['obt'], datetime.date.today().isoformat()))
        conn.commit()
        pdf_data = {
            "school_name": "GHS Bhutta Mohabbat",
            "emis": "123456",
            "district": "Some District",
            "student_name": name,
            "father_name": father,
            "roll": roll,
            "class": class_name,
            "section": section,
            "session": session,
            "position": position or "-",
            "marks_data": marks_data,
            "logo": logo
        }
        pdf_buffer = generate_pdf(pdf_data)
        st.success("Student saved! Download the PDF below:")
        st.download_button("Download Report Card", pdf_buffer, file_name=f"{name}_report.pdf", mime="application/pdf")
