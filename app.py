import streamlit as st
import fitz  # PyMuPDF
import io

# School Details
SCHOOL_NAME = "GOVT HIGH SCHOOL BHUTTA MOHABBAT"

st.set_page_config(page_title="GHS Bhutta Mohabbat Paper Tool")
st.title("📄 Professional Paper Branding Tool")
st.write(f"Ye tool aapke paper se website mita kar **{SCHOOL_NAME}** ka naam add kar dega.")

uploaded_file = st.file_uploader("PDF Paper Upload Karein", type="pdf")

if uploaded_file:
    # PDF ko read karna
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    
    for page in doc:
        w = page.rect.width
        h = page.rect.height
        
        # 1. PEHLE PURANI CHEEZON KO MITANA (White Boxes)
        header_rect = fitz.Rect(0, 0, w, 65) # Header saaf karne ke liye
        footer_rect = fitz.Rect(0, h - 60, w, h) # Footer saaf karne ke liye
        
        # Center Watermark area (aapki photo ke mutabiq)
        c_x, c_y = w / 2, h / 2
        watermark_rect = fitz.Rect(c_x - 130, c_y - 30, c_x + 130, c_y + 30)

        # In teeno jagaho par safaid patti pherna
        for area in [header_rect, footer_rect, watermark_rect]:
            page.draw_rect(area, color=(1, 1, 1), fill=(1, 1, 1))

        # 2. AB NAYA SCHOOL KA NAAM LIKHNA
        # Header (Top Center)
        page.insert_text(fitz.Point(w/2 - 145, 40), SCHOOL_NAME, 
                         fontsize=14, color=(0, 0, 0), fontname="helv-bold")
        
        # Footer (Bottom Center)
        page.insert_text(fitz.Point(w/2 - 120, h - 30), SCHOOL_NAME, 
                         fontsize=10, color=(0, 0, 0), fontname="helv")

        # Naya Watermark (Center - Halka Grey aur Tircha)
        # Rotate=15 isse ye bilkul official watermark lagega
        page.insert_text(fitz.Point(c_x - 160, c_y), SCHOOL_NAME, 
                         fontsize=18, color=(0.85, 0.85, 0.85), 
                         fontname="helv-bold", rotate=15)

    # Nayi File Save Karein
    output = io.BytesIO()
    doc.save(output)
    
    st.success("Mubarak ho! Aapka school branded paper tayyar hai.")
    st.download_button(
        label="Official School Paper Download Karein",
        data=output.getvalue(),
        file_name="GHS_Bhutta_Mohabbat_Paper.pdf",
        mime="application/pdf"
    )
