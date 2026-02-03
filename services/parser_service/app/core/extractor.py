"""
Text extraction from various document formats.
"""

import io
from typing import Optional


async def extract_text(content: bytes, extension: str, filename: str) -> dict:
    """
    Extract text from document bytes based on file extension.
    Falls back to OCR if text content is minimal.
    """
    extracted_text = ""
    method_used = "direct"

    if extension == ".pdf":
        extracted_text = extract_from_pdf(content)
    elif extension in {".docx", ".doc"}:
        extracted_text = extract_from_docx(content)
    elif extension in {".png", ".jpg", ".jpeg"}:
        # Image files go directly to OCR
        extracted_text = await extract_with_ocr(content, extension)
        method_used = "ocr"

    # Check if we need OCR fallback (less than 100 chars extracted)
    if len(extracted_text.strip()) < 100 and method_used == "direct":
        ocr_text = await extract_with_ocr(content, extension)
        if len(ocr_text.strip()) > len(extracted_text.strip()):
            extracted_text = ocr_text
            method_used = "ocr_fallback"

    return {
        "filename": filename,
        "text": extracted_text,
        "char_count": len(extracted_text),
        "method": method_used,
    }


def extract_from_pdf(content: bytes) -> str:
    """Extract text from PDF using PyMuPDF."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=content, filetype="pdf")
        text_parts = []

        for page in doc:
            text_parts.append(page.get_text())

        doc.close()
        return "\n".join(text_parts)
    except ImportError:
        return "[PDF extraction requires PyMuPDF - pip install pymupdf]"
    except Exception as e:
        return f"[PDF extraction error: {e}]"


def extract_from_docx(content: bytes) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        from docx import Document

        doc = Document(io.BytesIO(content))
        text_parts = []

        for paragraph in doc.paragraphs:
            text_parts.append(paragraph.text)

        return "\n".join(text_parts)
    except ImportError:
        return "[DOCX extraction requires python-docx - pip install python-docx]"
    except Exception as e:
        return f"[DOCX extraction error: {e}]"


async def extract_with_ocr(content: bytes, extension: Optional[str] = None) -> str:
    """
    Extract text using OCR (EasyOCR for Arabic+English support).
    """
    try:
        import easyocr
        import fitz  # PyMuPDF
        import numpy as np
        from PIL import Image

        # Initialize reader with English and Arabic
        reader = easyocr.Reader(["en", "ar"], gpu=False)

        def image_bytes_to_array(image_bytes: bytes) -> "np.ndarray":
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            return np.array(image)

        def ocr_image_array(image_array: "np.ndarray") -> list[str]:
            results = reader.readtext(image_array)
            return [result[1] for result in results]

        text_parts: list[str] = []

        if extension == ".pdf":
            # Render PDF pages to images before OCR
            doc = fitz.open(stream=content, filetype="pdf")
            try:
                for page in doc:
                    pix = page.get_pixmap(dpi=200)
                    mode = "RGB" if pix.alpha == 0 else "RGBA"
                    image = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                    if mode == "RGBA":
                        image = image.convert("RGB")
                    text_parts.extend(ocr_image_array(np.array(image)))
            finally:
                doc.close()
        else:
            text_parts.extend(ocr_image_array(image_bytes_to_array(content)))

        return "\n".join(text_parts)
    except ImportError:
        return "[OCR requires EasyOCR/PyMuPDF/Pillow/Numpy - ensure parser dependencies are installed]"
    except Exception as e:
        return f"[OCR error: {e}]"
