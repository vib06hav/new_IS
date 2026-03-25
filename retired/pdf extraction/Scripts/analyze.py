import sys
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTRect, LTFigure, LTCurve, LTLine

def analyze_pdf(pdf_path, output_path):
    print(f"Analyzing {pdf_path} into {output_path} (including Lines and Curves)...")
    with open(output_path, 'w', encoding='utf-8') as f:
        for page_layout in extract_pages(pdf_path):
            f.write(f"--- Page {page_layout.pageid} ---\n")
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    pass # ignore text for this check
                    # text = element.get_text().strip()
                    # if text:
                    #     f.write(f"TEXT: {text!r} @ {element.bbox}\n")
                elif isinstance(element, LTRect):
                    f.write(f"RECTANGLE: @ {element.bbox} (filled: {element.fill}, stroked: {element.stroke})\n")
                elif isinstance(element, LTLine):
                    f.write(f"LINE: @ {element.bbox} (linewidth: {element.linewidth})\n")
                elif isinstance(element, LTCurve):
                    f.write(f"CURVE: @ {element.bbox} (filled: {element.fill}, stroked: {element.stroke}, linewidth: {element.linewidth})\n")
                elif isinstance(element, LTFigure):
                    pass
                    # f.write(f"FIGURE: @ {element.bbox}\n")

if __name__ == '__main__':
    if len(sys.argv) > 2:
        analyze_pdf(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python analyze.py <pdf_path> <output_path>")
