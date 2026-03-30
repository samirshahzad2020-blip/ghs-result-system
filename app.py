import streamlit as st
import fitz  # PyMuPDF
import io

# اسکول کا نام جو ہر جگہ آئے گا
SCHOOL_NAME = "GOVT HIGH SCHOOL BHUTTA MOHABBAT"

st.set_page_config(page_title="GHS Bhutta Mohabbat - Paper Designer")
st.title("🎓 School Paper Branding Tool")
st.write(f"یہ ٹول آپ کے پیپر سے واٹر مارک ختم کر کے **{SCHOOL_NAME}** لکھ دے گا۔")

uploaded_file = st.file_uploader("اپنی PDF فائل یہاں اپ لوڈ کریں", type="pdf")

if uploaded_file:
    # PDF کو میموری میں کھولنا
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    
    for page in doc:
        w = page.rect.width
        h = page.rect.height
        
        # 1. پرانی تحریر مٹانے کے لیے سفید ڈبے (White Boxes)
        # ہیڈر (اوپر والی ویب سائٹ مٹانے کے لیے)
        header_rect = fitz.Rect(0, 0, w, 70) 
        # فوٹر (نیچے والی ویب سائٹ مٹانے کے لیے)
        footer_rect = fitz.Rect(0, h - 60, w, h) 
        # درمیان والا واٹر مارک (جو آپ نے تصویر میں دکھایا)
        c_x, c_y = w / 2, h / 2
        watermark_rect = fitz.Rect(c_x - 140, c_y - 35, c_x + 140, c_y + 35)

        # ان حصوں کو سفید رنگ سے بھر دیں
        for area in [header_rect, footer_rect, watermark_rect]:
            page.draw_rect(area, color=(1, 1, 1), fill=(1, 1, 1))

        # 2. اسکول کا نام لکھنا (Branding)
        
        # اوپر (Header) - بڑا اور واضح نام
        page.insert_text(fitz.Point(w/2 - 150, 45), SCHOOL_NAME, 
                         fontsize=15, color=(0, 0, 0), fontname="helv-bold")
        
        # نیچے (Footer) - چھوٹا نام
        page.insert_text(fitz.Point(w/2 - 120, h - 30), SCHOOL_NAME, 
                         fontsize=10, color=(0, 0, 0), fontname="helv")

        # نیا واٹر مارک (درمیان میں ہلکا سا رنگ اور تھوڑا ترچھا)
        # rotate=15 اسے پروفیشنل لک دے گا
        page.insert_text(fitz.Point(c_x - 170, c_y), SCHOOL_NAME, 
                         fontsize=20, color=(0.85, 0.85, 0.85), 
                         fontname="helv-bold", rotate=15)

    # نئی فائل کو اسٹریم لٹ میں ڈاؤن لوڈ کے لیے تیار کرنا
    output = io.BytesIO()
    doc.save(output)
    
    st.success("آپ کے اسکول کا آفیشل پیپر تیار ہے!")
    st.download_button(
        label="آفیشل پیپر ڈاؤن لوڈ کریں",
        data=output.getvalue(),
        file_name="GHS_Bhutta_Mohabbat_Final_Paper.pdf",
        mime="application/pdf"
    )
