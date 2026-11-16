"""Tesseract-backed image converter registered with Microsoft MarkItDown."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from markitdown import DocumentConverter, DocumentConverterResult

EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.webp'}

class LocalImageConverter(DocumentConverter):
    def accepts(self, file_stream, stream_info, **kwargs):
        return (stream_info.extension or '').lower() in EXTENSIONS

    def convert(self, file_stream, stream_info, **kwargs):
        from PIL import Image, ImageOps
        local = Path(__file__).parent / 'ocr/usr'
        binary = local / 'bin/tesseract'
        executable = str(binary) if binary.exists() else shutil.which('tesseract')
        if not executable:
            raise RuntimeError('Tesseract belum terpasang. Pasang tesseract-ocr, tesseract-ocr-ind, dan tesseract-ocr-eng.')
        env = os.environ.copy()
        if binary.exists():
            env['LD_LIBRARY_PATH'] = str(local / 'lib/x86_64-linux-gnu') + ':' + env.get('LD_LIBRARY_PATH', '')
            env['TESSDATA_PREFIX'] = str(local / 'share/tesseract-ocr/5/tessdata')
        language = kwargs.get('ocr_language', 'ind+eng')
        pages = []
        with tempfile.TemporaryDirectory(prefix='asnkit-ocr-') as folder:
            with Image.open(file_stream) as image:
                for index in range(getattr(image, 'n_frames', 1)):
                    image.seek(index)
                    rgba = ImageOps.exif_transpose(image).convert('RGBA')
                    page = Image.new('RGB', rgba.size, 'white')
                    page.paste(rgba, mask=rgba.getchannel('A'))
                    filename = Path(folder) / 'page.png'
                    page.save(filename)
                    result = subprocess.run([executable, str(filename), 'stdout', '-l', language],
                                            capture_output=True, text=True, encoding='utf-8', env=env, timeout=180)
                    if result.returncode:
                        raise RuntimeError(result.stderr.strip() or 'OCR gagal membaca gambar.')
                    if result.stdout.strip():
                        pages.append(result.stdout.strip())
        if not pages:
            raise ValueError('Tidak ada teks yang terbaca. Gunakan gambar yang jelas dan mengandung teks.')
        return DocumentConverterResult(markdown='\n\n'.join(pages))
