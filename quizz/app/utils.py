import os

try:
    from PyPDF2 import PdfReader
except Exception:  # pragma: no cover - PyPDF2 may not be installed
    PdfReader = None
try:
    from PIL import Image
    import pytesseract
except Exception:  # pragma: no cover - optional OCR dependencies
    Image = None
    pytesseract = None

def read_document_text(path: str) -> str:
    """Return UTF-8 text extracted from a document."""
    ext = os.path.splitext(path)[1].lower()
    if ext in {'.png', '.jpg', '.jpeg'} and Image and pytesseract:
        try:
            img = Image.open(path)
            return pytesseract.image_to_string(img)
        except Exception:
            return ''
    if path.lower().endswith('.pdf') and PdfReader is not None:
        try:
            reader = PdfReader(path)
            return "\n".join(page.extract_text() or '' for page in reader.pages)
        except Exception:
            return ''
    try:
        with open(path, 'rb') as f:
            data = f.read()
        return data.decode('utf-8', errors='ignore')
    except Exception:
        return ''
