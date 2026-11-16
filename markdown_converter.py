"""Local PDF-to-Markdown conversion using Microsoft MarkItDown."""
import os
from pathlib import Path
import sys
import tempfile


def convert_pdf(source, target, kind="pdf", language="ind+eng"):
    from markitdown import MarkItDown

    source, target = Path(source), Path(target)
    if source.resolve() == target.resolve():
        raise ValueError("File hasil harus berbeda dari file sumber.")
    converter = MarkItDown(enable_plugins=False)
    if kind == "image":
        from image_ocr import LocalImageConverter
        converter.register_converter(LocalImageConverter(), priority=-1)
    result = converter.convert_local(str(source), ocr_language=language)
    text = result.text_content
    if not text.strip():
        raise ValueError("Tidak ada teks yang dapat diekstrak. PDF hasil scan memerlukan OCR terlebih dahulu.")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent,
                                         prefix=".asnkit-", suffix=".tmp", delete=False) as out:
            temporary = Path(out.name)
            out.write(text)
            if not text.endswith("\n"):
                out.write("\n")
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return target


if __name__ == "__main__":
    try:
        convert_pdf(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "pdf", sys.argv[4] if len(sys.argv) > 4 else "ind+eng")
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
