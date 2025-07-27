import os
import re
import json
import traceback
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import Title, Header

def extract_outline(pdf_path):
    title = ""
    outline = []

    try:
        elements = partition_pdf(
            filename=pdf_path,
            extract_emphasized_text=True,
            strategy="hi_res",
            infer_table_structure=True
        )

        def get_font_weight(el):
            em = getattr(el.metadata, "emphasized_text_contents", []) or []
            return max((t.weight for t in em if hasattr(t, "weight")), default=0)

        def get_font_size(el):
            em = getattr(el.metadata, "emphasized_text_contents", []) or []
            return max((t.size for t in em if hasattr(t, "size")), default=0)

        # --- Detect and skip form-like PDFs ---
        numbered_on_page1 = 0
        for el in elements:
            if getattr(el.metadata, "page_number", 0) != 1:
                continue
            text = el.text.strip()
            if re.match(r'^\d+\.\s', text) and len(text.split()) < 6:
                numbered_on_page1 += 1
        is_form_like = numbered_on_page1 >= 4

        # --- Extract Title (page 1) ---
        candidates = []
        for idx, el in enumerate(elements):
            if getattr(el.metadata, "page_number", 0) != 1:
                continue
            text = el.text.strip()
            if not text or len(text.split()) < 3:
                continue

            font_size = get_font_size(el)
            font_weight = get_font_weight(el)
            score = font_size * 2 + font_weight
            score += max(100 - idx * 5, 0)
            candidates.append((score, text))

        if candidates:
            title = max(candidates, key=lambda x: x[0])[1]

        # --- Skip heading detection for form-style PDFs ---
        if is_form_like:
            return {"title": title.strip(), "outline": []}

        # --- Extract Headings (H1–H3) ---
        seen = set()
        for el in elements:
            text = el.text.strip()
            if not text or len(text) < 2:
                continue

            page = getattr(el.metadata, "page_number", 0)
            font_size = get_font_size(el)
            font_weight = get_font_weight(el)
            is_bold = font_weight >= 600
            is_large = font_size >= 11

            level = None

            if isinstance(el, Header) and getattr(el, "depth", 0) > 0:
                level = f"H{min(el.depth, 3)}"
            elif re.match(r'^\d+\.\d+\.\d+\s', text):
                level = "H3"
            elif re.match(r'^\d+\.\d+\s', text):
                level = "H2"
            elif re.match(r'^\d+\.\s', text) and len(text.split()) > 3:
                level = "H2"
            elif is_bold and is_large:
                if font_size >= 16:
                    level = "H1"
                elif font_size >= 13:
                    level = "H2"
                else:
                    level = "H3"
            elif text.isupper() and len(text.split()) > 2:
                level = "H1"

            if level:
                key = f"{text}-{page}"
                if key not in seen:
                    seen.add(key)
                    outline.append({
                        "level": level,
                        "text": text,
                        "page": page
                    })

    except Exception as e:
        return {"title": "", "outline": [], "error": str(e)}

    return {
        "title": title.strip(),
        "outline": outline
    }

def process_pdfs_in_directory(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(".pdf"):
            continue

        print(f"Processing {filename}...")
        input_path = os.path.join(input_dir, filename)
        result = extract_outline(input_path)

        output_file = os.path.splitext(filename)[0] + ".json"
        output_path = os.path.join(output_dir, output_file)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        print(f"Saved {output_file}")

if __name__ == "__main__":
    INPUT_DIR = "/app/input"
    OUTPUT_DIR = "/app/output"
    process_pdfs_in_directory(INPUT_DIR, OUTPUT_DIR)
