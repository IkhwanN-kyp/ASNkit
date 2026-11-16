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
                    options = kwargs.get('ocr_options', {})
                    regions = options.get('regions') or [[0,0,1,1]]
                    layout = options.get('layout', 'auto')
                    blocks = []
                    for x1,y1,x2,y2 in regions:
                        if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
                            raise ValueError('Area OCR tidak valid.')
                        crop = page.crop((round(x1*page.width), round(y1*page.height), round(x2*page.width), round(y2*page.height)))
                        if layout == 'columns':
                            split = float(options.get('split', .5))
                            if not .2 <= split <= .8:
                                raise ValueError('Batas kolom tidak valid.')
                            mid = round(crop.width*split)
                            blocks.extend([crop.crop((0,0,mid,crop.height)), crop.crop((mid,0,crop.width,crop.height))])
                        else:
                            blocks.append(crop)
                    for block in blocks:
                        # Enlarge small printed text and balance photo contrast, without altering the original.
                        gray = ImageOps.autocontrast(ImageOps.grayscale(block), cutoff=1)
                        scale = min(2., 2200 / max(gray.size))
                        if scale > 1:
                            gray = gray.resize((round(gray.width*scale), round(gray.height*scale)), Image.Resampling.LANCZOS)
                        filename = Path(folder) / 'page.png'
                        gray.save(filename)
                        psm = '6' if layout == 'block' else '3'
                        result = subprocess.run([executable, str(filename), 'stdout', '-l', language, '--psm', psm],
                                                capture_output=True, text=True, encoding='utf-8', env=env, timeout=180)
                        if result.returncode:
                            raise RuntimeError(result.stderr.strip() or 'OCR gagal membaca gambar.')
                        if result.stdout.strip():
                            pages.append(result.stdout.strip())
        if not pages:
            raise ValueError('Tidak ada teks yang terbaca. Gunakan gambar yang jelas dan mengandung teks.')
        return DocumentConverterResult(markdown='\n\n'.join(pages))
