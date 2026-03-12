import fitz

doc = fitz.open('Original PDF/Dummy App (5).pdf')

with open('Dumps/xobject_diagnostic.txt', 'w', encoding='utf-8') as f:
    for page in doc:
        f.write(f"\n=== Page {page.number} ===\n")
        
        # Check for XObjects on this page
        xref_list = page.get_images(full=True)
        f.write(f"  Images: {len(xref_list)}\n")
        for img in xref_list:
            f.write(f"    Image xref={img[0]}, name={img[7]}, size={img[2]}x{img[3]}, cs={img[5]}\n")
        
        # Check for Form XObjects
        # page.xref is the page's own xref number
        f.write(f"  Page xref: {page.xref}\n")
        
        # Get all XObjects referenced by this page
        xobjects = page.get_xobjects()
        f.write(f"  XObjects: {len(xobjects)}\n")
        for xobj in xobjects:
            f.write(f"    XObject: xref={xobj[0]}, name={xobj[1]}\n")
            
            # Try to read the XObject's content stream
            try:
                xobj_stream = doc.xref_stream(xobj[0])
                if xobj_stream:
                    # Look for black fill commands in the stream
                    stream_text = xobj_stream.decode('latin-1', errors='replace')
                    # Check for "0 0 0 rg" (black fill) or "0 g" (grayscale black)
                    has_black_fill = '0 0 0 rg' in stream_text or '0 g' in stream_text
                    has_rect = ' re' in stream_text
                    has_fill = ' f' in stream_text
                    f.write(f"      Stream length: {len(xobj_stream)}\n")
                    f.write(f"      Has black fill cmd: {has_black_fill}\n")
                    f.write(f"      Has rect cmd: {has_rect}\n")
                    f.write(f"      Has fill cmd: {has_fill}\n")
                    
                    if has_black_fill and has_rect:
                        # Dump first 500 chars of stream for inspection
                        f.write(f"      Stream preview: {stream_text[:800]}\n")
            except Exception as e:
                f.write(f"      Error reading stream: {e}\n")

print("Done - check Dumps/xobject_diagnostic.txt")
