# 📄 OCR Zone Tool (Streamlit)

A web-based tool to manually define OCR zones on images or PDFs and extract text with Tesseract OCR. Built with Streamlit.

---

## 🚀 Features

- Upload images or PDFs
- Manually define OCR zones
- Zoom in/out per page
- Multi-page PDF navigation
- Extract text per zone using Tesseract
- Export results as Excel or CSV

---

## 🧰 Requirements

- Python 3.8+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [Poppler](http://blog.alivate.com.au/poppler-windows/) for PDF support

Add Tesseract and Poppler paths to your environment variables.

---

## 🔧 Setup

```bash
# Clone repo
git clone https://github.com/yourusername/ocr-zone-tool.git
cd ocr-zone-tool

# (Optional) Create a virtual environment
python -m venv venv
venv\Scripts\activate  # on Windows

# Install dependencies
pip install -r requirements.txt
