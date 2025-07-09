import streamlit as st 
import cv2
import numpy as np
from PIL import Image
import pandas as pd
import pytesseract
from pdf2image import convert_from_path
import io
import base64

# Configure page
st.set_page_config(
    page_title="PDF/Image OCR Zone Tool",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .zone-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'pages' not in st.session_state:
    st.session_state.pages = []
if 'zones' not in st.session_state:
    st.session_state.zones = {}
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0
if 'zoom_level' not in st.session_state:
    st.session_state.zoom_level = 1.0

def main():
    st.markdown('<div class="main-header"><h1>📄 PDF/Image OCR Zone Tool</h1><p>Upload, define zones, and extract text with OCR</p></div>', unsafe_allow_html=True)

    with st.sidebar:
        st.header("📁 File Upload")
        uploaded_file = st.file_uploader("Choose a PDF or image file", type=['pdf', 'png', 'jpg', 'jpeg', 'bmp', 'tiff'])
        if uploaded_file:
            load_file(uploaded_file)

        if st.session_state.pages:
            st.header("📑 Page Navigation")
            page_num = st.selectbox("Select page", range(len(st.session_state.pages)), format_func=lambda x: f"Page {x + 1}", key="page_selector")
            st.session_state.current_page = page_num

            st.header("🔍 Zoom Controls")
            zoom = st.slider("Zoom Level", 0.5, 3.0, st.session_state.zoom_level, 0.1)
            st.session_state.zoom_level = zoom

            st.header("📊 Zone Management")
            if st.button("Clear Current Page Zones", type="secondary"):
                if st.session_state.current_page in st.session_state.zones:
                    del st.session_state.zones[st.session_state.current_page]
                    st.success("Current page zones cleared!")
                    st.rerun()

            if st.button("Clear All Zones", type="secondary"):
                st.session_state.zones = {}
                st.success("All zones cleared!")
                st.rerun()

    if st.session_state.pages:
        col1, col2 = st.columns([3, 1])

        with col1:
            display_image_with_zones()

        with col2:
            zone_management_panel()
    else:
        st.info("👆 Please upload a PDF or image file to begin")

def load_file(uploaded_file):
    try:
        if uploaded_file.type == "application/pdf":
            pdf_bytes = uploaded_file.read()
            pages = convert_from_path(io.BytesIO(pdf_bytes))
            st.session_state.pages = pages
        else:
            image = Image.open(uploaded_file)
            st.session_state.pages = [image]

        st.session_state.current_page = 0
        st.session_state.zones = {}
        st.session_state.zoom_level = 1.0

        st.success(f"✅ Loaded {len(st.session_state.pages)} page(s)")

    except Exception as e:
        st.error(f"❌ Error loading file: {str(e)}")

def display_image_with_zones():
    if not st.session_state.pages:
        return

    current_page = st.session_state.pages[st.session_state.current_page]

    width, height = current_page.size
    new_width = int(width * st.session_state.zoom_level)
    new_height = int(height * st.session_state.zoom_level)

    if st.session_state.zoom_level != 1.0:
        display_image = current_page.resize((new_width, new_height), Image.LANCZOS)
    else:
        display_image = current_page

    cv_image = cv2.cvtColor(np.array(display_image), cv2.COLOR_RGB2BGR)

    page_zones = st.session_state.zones.get(st.session_state.current_page, [])
    for i, zone in enumerate(page_zones):
        x1, y1, x2, y2 = zone
        scaled_coords = (int(x1 * st.session_state.zoom_level), int(y1 * st.session_state.zoom_level), int(x2 * st.session_state.zoom_level), int(y2 * st.session_state.zoom_level))
        cv2.rectangle(cv_image, scaled_coords[:2], scaled_coords[2:], (0, 0, 255), 2)
        cv2.putText(cv_image, f"Zone {i+1}", (scaled_coords[0], scaled_coords[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    final_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
    st.image(final_image, use_column_width=True)

def zone_management_panel():
    st.subheader("🎯 Zone Management")
    with st.expander("➕ Add Zone Manually"):
        st.write("Define zone coordinates (in original image pixels):")
        col1, col2 = st.columns(2)
        with col1:
            x1 = st.number_input("X1", min_value=0, value=0, key="x1")
            y1 = st.number_input("Y1", min_value=0, value=0, key="y1")
        with col2:
            x2 = st.number_input("X2", min_value=0, value=100, key="x2")
            y2 = st.number_input("Y2", min_value=0, value=100, key="y2")

        if st.button("Add Zone"):
            if x2 > x1 and y2 > y1:
                page_num = st.session_state.current_page
                if page_num not in st.session_state.zones:
                    st.session_state.zones[page_num] = []
                st.session_state.zones[page_num].append((x1, y1, x2, y2))
                st.success("Zone added!")
                st.rerun()
            else:
                st.error("Invalid coordinates! X2 > X1 and Y2 > Y1")

    page_zones = st.session_state.zones.get(st.session_state.current_page, [])
    if page_zones:
        st.write(f"**Current Page Zones ({len(page_zones)}):**")
        for i, zone in enumerate(page_zones):
            x1, y1, x2, y2 = zone
            with st.container():
                st.markdown(f'<div class="zone-card">', unsafe_allow_html=True)
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Zone {i+1}:** ({int(x1)}, {int(y1)}) → ({int(x2)}, {int(y2)})")
                    st.write(f"Size: {int(x2-x1)} × {int(y2-y1)} pixels")
                with col2:
                    if st.button("🗑️", key=f"delete_{i}", help="Delete zone"):
                        st.session_state.zones[st.session_state.current_page].pop(i)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("🔍 OCR Processing")
    total_zones = sum(len(zones) for zones in st.session_state.zones.values())
    st.write(f"**Total zones across all pages:** {total_zones}")

    if total_zones > 0:
        if st.button("🚀 Run OCR on All Zones", type="primary"):
            run_ocr_processing()
    else:
        st.info("Add some zones first to run OCR")

def run_ocr_processing():
    if not st.session_state.zones:
        st.warning("No zones defined!")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()

    all_results = []
    total_zones = sum(len(zones) for zones in st.session_state.zones.values())
    processed = 0

    try:
        for page_num, zones in st.session_state.zones.items():
            page_image = st.session_state.pages[page_num]
            cv_image = cv2.cvtColor(np.array(page_image), cv2.COLOR_RGB2BGR)

            for zone in zones:
                status_text.text(f"Processing zone {processed + 1} of {total_zones}...")

                x1, y1, x2, y2 = zone
                height, width = cv_image.shape[:2]
                x1 = max(0, min(int(x1), width))
                y1 = max(0, min(int(y1), height))
                x2 = max(0, min(int(x2), width))
                y2 = max(0, min(int(y2), height))

                if x2 > x1 and y2 > y1:
                    cropped = cv_image[y1:y2, x1:x2]
                    text = pytesseract.image_to_string(cropped, config='--psm 6')
                    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
                    all_results.append({
                        'Page': page_num + 1,
                        'Zone': len(all_results) + 1,
                        'Text': '\n'.join(lines) if lines else '',
                        'Coordinates': f"({x1},{y1}) to ({x2},{y2})"
                    })

                processed += 1
                progress_bar.progress(processed / total_zones)

        if all_results:
            st.markdown('<div class="success-box"><h3>✅ OCR Results</h3></div>', unsafe_allow_html=True)
            df = pd.DataFrame(all_results)
            st.dataframe(df, use_container_width=True)
            col1, col2 = st.columns(2)

            with col1:
                excel_buffer = io.BytesIO()
                df.to_excel(excel_buffer, index=False)
                excel_buffer.seek(0)
                st.download_button("📥 Download Excel", data=excel_buffer, file_name="ocr_results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            with col2:
                csv = df.to_csv(index=False)
                st.download_button("📥 Download CSV", data=csv, file_name="ocr_results.csv", mime="text/csv")

            st.subheader("🔍 Zone Previews")
            for i, result in enumerate(all_results):
                with st.expander(f"Zone {result['Zone']} - Page {result['Page']}"):
                    st.write(f"**Coordinates:** {result['Coordinates']}")
                    st.write(f"**Extracted Text:**")
                    st.code(result['Text'] if result['Text'] else "No text found")

        else:
            st.warning("No text extracted from any zones!")

    except Exception as e:
        st.error(f"Error during OCR processing: {str(e)}")

    finally:
        progress_bar.empty()
        status_text.empty()

if __name__ == "__main__":
    main()
