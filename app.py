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
