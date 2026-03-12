import sys
import fitz

def print_stream(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[0]
    contents = page.read_contents()
    with open("stream.txt", "w", encoding="utf-8") as f:
        f.write(contents.decode('latin-1'))
    print("Wrote content stream to stream.txt")

if __name__ == '__main__':
    print_stream(sys.argv[1])
