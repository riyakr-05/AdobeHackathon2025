import os
import sys
import json
from datetime import datetime
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import Header, NarrativeText
from sentence_transformers import SentenceTransformer, util

# === Accept collection name from CLI ===
if len(sys.argv) < 2:
    print("❌ Error: Collection name not provided.")
    sys.exit(1)

collection = sys.argv[1]
input_dir = os.path.join(collection, "input")
output_dir = os.path.join(collection, "output")
os.makedirs(output_dir, exist_ok=True)

# === Load persona ===
persona_path = os.path.join(input_dir, "persona.json")
if not os.path.exists(persona_path):
    print(f"❌ Error: persona.json not found at {persona_path}")
    sys.exit(1)

with open(persona_path, "r", encoding="utf-8") as f:
    persona_input = json.load(f)

# === Load sentence transformer model ===
model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

# Format the persona and job to get persona embedding
persona_text = f"{persona_input.get('role', '')} — {persona_input.get('task', '')}"
persona_embedding = model.encode(persona_text, convert_to_tensor=True)

# === Output structure ===
output = {
    "metadata": {
        "documents": [],
        "persona": persona_input.get("role", ""),
        "job": persona_input.get("task", ""),
        "timestamp": datetime.utcnow().isoformat()
    },
    "extracted_sections": [],
    "subsection_analysis": []
}

# === Process single PDF file ===
def process_pdf(filepath):
    try:
        elements = partition_pdf(
            filename=filepath,
            extract_emphasized_text=True,
            strategy="hi_res",
            infer_table_structure=True
        )
    except Exception as e:
        print(f"⚠️ Failed to process {filepath}: {e}")
        return []

    section_data = []
    filename = os.path.basename(filepath)

    for el in elements:
        if isinstance(el, Header) or isinstance(el, NarrativeText):
            text = el.text.strip()
            if len(text) < 10:
                continue
            embedding = model.encode(text, convert_to_tensor=True)
            similarity = util.cos_sim(persona_embedding, embedding).item()

            section_data.append({
                "document": filename,
                "page": el.metadata.page_number or 0,
                "section_title": text if isinstance(el, Header) else "Paragraph",
                "refined_text": text,
                "score": similarity
            })

    return section_data

# === Process all PDFs in input directory ===
for file in os.listdir(input_dir):
    if not file.lower().endswith(".pdf"):
        continue

    pdf_path = os.path.join(input_dir, file)
    output["metadata"]["documents"].append(file)

    sections = process_pdf(pdf_path)
    top_sections = sorted(sections, key=lambda x: x["score"], reverse=True)[:5]

    for rank, section in enumerate(top_sections, start=1):
        output["extracted_sections"].append({
            "document": section["document"],
            "page": section["page"],
            "section_title": section["section_title"],
            "importance_rank": rank
        })
        output["subsection_analysis"].append({
            "document": section["document"],
            "page": section["page"],
            "refined_text": section["refined_text"]
        })

# === Save output ===
result_path = os.path.join(output_dir, "result.json")
with open(result_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print(f"✅ Done. Output saved to {result_path}")
