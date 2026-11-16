"""Local PDF-to-Markdown conversion using Microsoft MarkItDown."""
import os
from pathlib import Path
import sys
import tempfile


def convert_pdf(source, target):
    from markitdown import MarkItDown

    source, target = Path(source), Path(target)
    if source.resolve() == target.resolve():
        raise ValueError("File hasil harus berbeda dari file sumber.")
    result = MarkItDown(enable_plugins=False).convert_local(str(source))
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
        convert_pdf(sys.argv[1], sys.argv[2])
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
