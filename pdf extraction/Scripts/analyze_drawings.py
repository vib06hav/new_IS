import sys
import fitz

def analyze_drawings(pdf_path, output_path):
    print(f"Analyzing drawings in {pdf_path} into {output_path}...")
    doc = fitz.open(pdf_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        for page_num in range(len(doc)):
            page = doc[page_num]
            f.write(f"--- Page {page_num + 1} ---\n")
            drawings = page.get_drawings()
            for i, d in enumerate(drawings):
                f.write(f"Drawing {i}:\n")
                f.write(f"  rect: {d['rect']}\n")
                f.write(f"  type: {d['type']}\n") # 'f' for fill, 's' for stroke, 'fs' for fill+stroke
                f.write(f"  fill: {d.get('fill')} (opacity: {d.get('fill_opacity')})\n")
                f.write(f"  color: {d.get('color')}\n")
                f.write(f"  width: {d.get('width')}\n")
            break  # Just first page

if __name__ == '__main__':
    analyze_drawings(sys.argv[1], sys.argv[2])
