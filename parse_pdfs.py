
import os
import json
import sys

# Add the project root to sys.path to allow imports from 'app'
sys.path.append(os.getcwd())

from app.agents.layout_extractor import extract_layout_blocks

def parse_all_pdfs():
    pdf_dir = os.path.join("tests", "pdfs")
    output_dir = os.path.join("tests", "raw_layouts")
    os.makedirs(output_dir, exist_ok=True)

    pdfs = [
        "Dummy App (1)_v8_filled.pdf",
        "Dummy App (2)_v8_filled.pdf",
        "Dummy App (3)_v8_filled.pdf",
        "Dummy App (5)_v8_filled.pdf",
        "Dummy App (8)_v8_filled.pdf"
    ]

    results = {}
    for pdf_name in pdfs:
        pdf_path = os.path.join(pdf_dir, pdf_name)
        print(f"Parsing {pdf_name}...")
        try:
            layout_data = extract_layout_blocks(pdf_path)
            output_filename = pdf_name.replace(".pdf", "_layout.json")
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(layout_data, f, indent=2, ensure_ascii=False)
            
            print(f"Saved to {output_path}")
            results[pdf_name] = output_path
        except Exception as e:
            print(f"Error parsing {pdf_name}: {e}")

    return results

if __name__ == "__main__":
    parse_all_pdfs()
