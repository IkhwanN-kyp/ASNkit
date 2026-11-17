import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QPointF, QProcess, QProcessEnvironment
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QLineEdit, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton,
    QSpinBox, QTabWidget, QVBoxLayout, QWidget,
)

APP_NAME = "ASNkit"
APP_VERSION = "1.3.0"
DONATION_URL = "https://trakteer.id/radarswingid"

BG = "#101820"
PANEL = "#182630"
PANEL_2 = "#223640"
TEXT = "#edf4f4"
MUTED = "#9db0b4"
TEAL = "#00d4aa"
TEAL_DARK = "#00a987"
LIGHT_BG = "#f2f6f7"
LIGHT_PANEL = "#ffffff"
LIGHT_PANEL_2 = "#e7eff1"
LIGHT_TEXT = "#17252b"
LIGHT_MUTED = "#596b72"


def pdf_files(paths):
    result = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            result.extend(sorted(x for x in p.iterdir() if x.is_file() and x.suffix.lower() == ".pdf"))
        elif p.is_file() and p.suffix.lower() == ".pdf":
            result.append(p)
    return result


class DropList(QListWidget):
    def __init__(self, extensions=None, multiple=True):
        super().__init__()
        self.extensions = extensions
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragDropMode(QListWidget.DragDrop)
        self.setSelectionMode(QListWidget.ExtendedSelection if multiple else QListWidget.SingleSelection)
        self.setSpacing(5)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
            self.add_paths(paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def add_paths(self, paths):
        for p in paths:
            path = Path(p)
            candidates = list(path.iterdir()) if path.is_dir() and self.extensions == {".pdf"} else [path]
            for candidate in candidates:
                if not candidate.is_file() or (self.extensions and candidate.suffix.lower() not in self.extensions):
                    continue
                existing = {self.item(i).data(Qt.UserRole) for i in range(self.count())}
                if str(candidate.resolve()) in existing:
                    continue
                item = QListWidgetItem(candidate.name)
                item.setToolTip(str(candidate))
                item.setData(Qt.UserRole, str(candidate.resolve()))
                self.addItem(item)

    def paths(self):
        return [Path(self.item(i).data(Qt.UserRole)) for i in range(self.count())]


class PdfToolkit(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — PDF Toolkit")
        self.resize(1020, 740)
        self.setMinimumSize(900, 680)
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(32, 26, 32, 28)
        layout.setSpacing(18)

        header = QHBoxLayout()
        brand = QLabel("◈")
        brand.setObjectName("brand")
        brand.setFixedWidth(44)
        title_col = QVBoxLayout()
        title = QLabel(APP_NAME)
        title.setObjectName("title")
        subtitle = QLabel("PDF tools sederhana, langsung dari desktop")
        subtitle.setObjectName("muted")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addWidget(brand)
        header.addLayout(title_col)
        header.addStretch()
        self.theme_picker = QComboBox()
        self.theme_picker.addItems(["Gelap", "Terang"])
        self.theme_picker.setToolTip("Pilih tema tampilan")
        self.theme_picker.currentIndexChanged.connect(self.apply_theme)
        header.addWidget(self.theme_picker, alignment=Qt.AlignTop)
        badge = QLabel("LOKAL + GEMINI")
        badge.setObjectName("badge")
        badge.setToolTip("Alat PDF dan OCR berjalan lokal. Tab Gemini mengirim gambar ke Google setelah persetujuan Anda.")
        header.addWidget(badge, alignment=Qt.AlignTop)
        layout.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.make_combine(), "Gabung PDF")
        self.tabs.addTab(self.make_split(), "Split PDF")
        self.tabs.addTab(self.make_pdf_word(), "PDF ↔ Word")
        self.tabs.addTab(self.make_markdown(), "PDF → Markdown")
        self.tabs.addTab(self.make_image_markdown(), "Gambar → MD")
        self.tabs.addTab(self.make_gemini(), "Gemini → MD")
        self.tabs.addTab(self.make_images(), "Gambar → PDF")
        self.tabs.addTab(self.make_viewer(), "PDF Viewer")
        self.tabs.addTab(self.make_about(), "Tentang")
        layout.addWidget(self.tabs, 1)
        self.status = QLabel("Pilih tab, tambahkan file, lalu jalankan proses.")
        self.status.setObjectName("muted")
        layout.addWidget(self.status)
        self.apply_theme(self.theme_picker.currentIndex())

    def apply_theme(self, index):
        light = index == 1
        bg, panel, panel2 = (LIGHT_BG, LIGHT_PANEL, LIGHT_PANEL_2) if light else (BG, PANEL, PANEL_2)
        fg, muted = (LIGHT_TEXT, LIGHT_MUTED) if light else (TEXT, MUTED)
        inset = "#ffffff" if light else "#111d24"
        border = "#b9cbd0" if light else "#38505a"
        self.setStyleSheet(f"""
            QWidget#root {{ background: {bg}; color: {fg}; font-family: 'DejaVu Sans'; font-size: 10pt; }}
            QWidget {{ color: {fg}; }}
            QMainWindow, QMenuBar {{ background: {bg}; color: {fg}; }}
            QLabel#brand {{ color: {TEAL_DARK if light else TEAL}; font-size: 30pt; font-weight: 700; }}
            QLabel#title {{ font-size: 22pt; font-weight: 700; }}
            QLabel {{ color: {fg}; }}
            QLabel#muted {{ color: {muted}; }}
            QLabel#aboutText {{ color: {fg}; line-height: 1.45; }}
            QLabel#aboutText a {{ color: {TEAL_DARK if light else TEAL}; font-weight: 600; }}
            QLabel#badge {{ color: {TEAL_DARK}; background: {'#e0f6ef' if light else '#15372f'}; border: 1px solid {'#8ccfba' if light else '#246456'}; border-radius: 10px; padding: 7px 11px; font-size: 8pt; font-weight: 700; }}
            QTabWidget::pane {{ border: 1px solid {border}; border-radius: 12px; background: {panel}; top: -1px; }}
            QTabBar::tab {{ background: transparent; color: {muted}; padding: 12px 10px; margin-right: 2px; font-weight: 600; }}
            QTabBar::tab:selected {{ color: {TEAL_DARK if light else TEAL}; border-bottom: 2px solid {TEAL}; }}
            QLabel#section {{ font-size: 15pt; font-weight: 650; }}
            QListWidget {{ background: {inset}; border: 1px dashed {border}; border-radius: 10px; padding: 10px; color: {fg}; }}
            QListWidget::item {{ background: {panel2}; border-radius: 6px; padding: 9px; }}
            QPushButton {{ background: {panel2}; color: {fg}; border: 1px solid {border}; border-radius: 8px; padding: 10px 14px; font-weight: 600; }}
            QPushButton:hover {{ border-color: {TEAL}; color: {TEAL_DARK if light else TEAL}; }}
            QPushButton#primary {{ background: {TEAL}; color: #06221c; border: 0; font-weight: 750; padding: 12px 18px; }}
            QPushButton#primary:hover {{ background: {TEAL_DARK}; color: white; }}
            QComboBox, QLineEdit, QSpinBox {{ background: {inset}; color: {fg}; border: 1px solid {border}; border-radius: 7px; padding: 8px; }}
            QComboBox QAbstractItemView {{ background: {panel}; color: {fg}; selection-background-color: {TEAL_DARK}; }}
        """)
        if hasattr(self, "pdf_view"):
            self.pdf_view.setStyleSheet(f"background: {inset}; border: 1px solid {border}; border-radius: 8px;")

    def page(self, heading, hint):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(22, 22, 22, 20)
        v.setSpacing(12)
        h = QLabel(heading)
        h.setObjectName("section")
        d = QLabel(hint)
        d.setObjectName("muted")
        v.addWidget(h)
        v.addWidget(d)
        return w, v

    def file_controls(self, listing, add_label="Tambah file"):
        row = QHBoxLayout()
        add = QPushButton(add_label)
        remove = QPushButton("Hapus pilihan")
        clear = QPushButton("Kosongkan")
        remove.clicked.connect(lambda: [listing.takeItem(listing.row(i)) for i in listing.selectedItems()])
        clear.clicked.connect(listing.clear)
        add.clicked.connect(lambda: self.pick_files(listing))
        row.addWidget(add)
        row.addWidget(remove)
        row.addWidget(clear)
        row.addStretch()
        return row

    def pick_files(self, listing):
        if listing in (getattr(self, "image_markdown_list", None), getattr(self, "gemini_list", None)):
            files, _ = QFileDialog.getOpenFileNames(self, "Pilih gambar", "", "Gambar (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp)")
        elif listing.extensions == {".pdf"}:
            files, _ = QFileDialog.getOpenFileNames(self, "Pilih file PDF", "", "PDF (*.pdf)")
        elif listing.extensions == {".docx"}:
            files, _ = QFileDialog.getOpenFileNames(self, "Pilih dokumen Word", "", "Word (*.docx)")
        else:
            files, _ = QFileDialog.getOpenFileNames(self, "Pilih gambar", "", "Gambar (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        listing.add_paths(files)

    def make_combine(self):
        w, v = self.page("Gabungkan beberapa PDF", "Seret file ke area di bawah. Urutan daftar menentukan urutan halaman pada hasil.")
        listing = DropList({".pdf"})
        v.addWidget(listing, 1)
        v.addLayout(self.file_controls(listing))
        row = QHBoxLayout()
        row.addStretch()
        run = QPushButton("Gabungkan PDF")
        run.setObjectName("primary")
        run.clicked.connect(lambda: self.combine(listing))
        row.addWidget(run)
        v.addLayout(row)
        return w

    def make_split(self):
        w, v = self.page("Pisahkan PDF", "Pisahkan semua halaman menjadi file terpisah atau ambil rentang halaman tertentu.")
        listing = DropList({".pdf"}, multiple=False)
        v.addWidget(listing, 1)
        v.addLayout(self.file_controls(listing))
        form = QFormLayout()
        self.split_mode = QComboBox()
        self.split_mode.addItems(["Satu file untuk setiap halaman", "Ambil rentang halaman"])
        self.page_start = QSpinBox(); self.page_start.setMinimum(1); self.page_start.setValue(1)
        self.page_end = QSpinBox(); self.page_end.setMinimum(1); self.page_end.setValue(1)
        form.addRow("Mode", self.split_mode)
        form.addRow("Dari halaman", self.page_start)
        form.addRow("Sampai halaman", self.page_end)
        v.addLayout(form)
        row = QHBoxLayout(); row.addStretch()
        run = QPushButton("Split PDF"); run.setObjectName("primary")
        run.clicked.connect(lambda: self.split(listing))
        row.addWidget(run); v.addLayout(row)
        return w

    def make_pdf_word(self):
        w, v = self.page("PDF ↔ Word", "Konversi PDF ke DOCX atau DOCX ke PDF. Tata letak kompleks mungkin berubah.")
        self.conversion_mode = QComboBox()
        self.conversion_mode.addItems(["PDF ke Word (.docx)", "Word (.docx) ke PDF"])
        v.addWidget(self.conversion_mode)
        self.convert_list = DropList({".pdf"})
        self.conversion_mode.currentIndexChanged.connect(self.update_convert_extensions)
        v.addWidget(self.convert_list, 1)
        v.addLayout(self.file_controls(self.convert_list))
        row = QHBoxLayout(); row.addStretch()
        run = QPushButton("Konversi"); run.setObjectName("primary")
        run.clicked.connect(self.convert_documents)
        row.addWidget(run); v.addLayout(row)
        return w

    def update_convert_extensions(self, index):
        self.convert_list.clear()
        self.convert_list.extensions = {".pdf"} if index == 0 else {".docx"}

    def make_markdown(self):
        w, v = self.page("PDF ke Markdown", "Ubah satu PDF menjadi file .md menggunakan Microsoft MarkItDown, langsung di komputer Anda.")
        self.markdown_list = DropList({".pdf"}, multiple=False)
        v.addWidget(self.markdown_list, 1)
        v.addLayout(self.file_controls(self.markdown_list))
        hint = QLabel("Hasil berupa teks Markdown, bukan salinan tata letak PDF. PDF hasil scan memerlukan OCR terlebih dahulu.")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        v.addWidget(hint)
        row = QHBoxLayout()
        row.addStretch()
        self.markdown_button = QPushButton("Simpan sebagai Markdown")
        self.markdown_button.setObjectName("primary")
        self.markdown_button.setMinimumWidth(245)
        self.markdown_button.clicked.connect(self.convert_markdown)
        row.addWidget(self.markdown_button)
        v.addLayout(row)
        self.markdown_process = None
        return w

    def make_image_markdown(self):
        w, v = self.page("Gambar ke Markdown", "Baca teks dari gambar dengan OCR lokal dan simpan sebagai Markdown melalui MarkItDown.")
        self.image_markdown_list = DropList({".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}, multiple=False)
        v.addWidget(self.image_markdown_list, 1)
        v.addLayout(self.file_controls(self.image_markdown_list))
        self.ocr_language = QComboBox()
        self.ocr_language.addItem("Indonesia + Inggris", "ind+eng")
        self.ocr_language.addItem("Indonesia", "ind")
        self.ocr_language.addItem("Inggris", "eng")
        v.addWidget(self.ocr_language)
        self.ocr_regions = []
        self.ocr_region_source = None
        region_row = QHBoxLayout()
        choose = QPushButton("Pilih area baca…")
        choose.clicked.connect(self.choose_ocr_regions)
        self.ocr_region_label = QLabel("Seluruh gambar")
        reset = QPushButton("Reset area")
        reset.clicked.connect(self.reset_ocr_regions)
        region_row.addWidget(choose); region_row.addWidget(self.ocr_region_label, 1); region_row.addWidget(reset)
        v.addLayout(region_row)
        self.ocr_layout = QComboBox()
        self.ocr_layout.addItem("Susunan otomatis", "auto")
        self.ocr_layout.addItem("Satu blok teks per area", "block")
        self.ocr_layout.addItem("Dua kolom: kiri lalu kanan (per area)", "columns")
        v.addWidget(self.ocr_layout)
        split_row = QHBoxLayout()
        split_row.addWidget(QLabel("Batas kolom (% lebar area)"))
        self.ocr_split = QSpinBox()
        self.ocr_split.setRange(20, 80); self.ocr_split.setValue(50)
        self.ocr_split.setEnabled(False)
        self.ocr_layout.currentIndexChanged.connect(lambda: self.ocr_split.setEnabled(self.ocr_layout.currentData() == "columns"))
        split_row.addWidget(self.ocr_split); split_row.addStretch()
        v.addLayout(split_row)
        self.image_markdown_list.itemSelectionChanged.connect(self.update_ocr_region_label)
        self.image_markdown_list.model().rowsInserted.connect(self.update_ocr_region_label)
        self.image_markdown_list.model().rowsRemoved.connect(self.update_ocr_region_label)
        hint = QLabel("Pilih satu gambar yang mengandung teks. Diproses lokal tanpa API key. Hasil OCR perlu diperiksa, terutama tabel dan tulisan tangan.")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        v.addWidget(hint)
        self.image_markdown_button = QPushButton("Simpan gambar sebagai Markdown")
        self.image_markdown_button.setObjectName("primary")
        self.image_markdown_button.setMinimumWidth(300)
        self.image_markdown_button.clicked.connect(lambda: self.convert_markdown("image"))
        v.addWidget(self.image_markdown_button)
        return w

    def make_gemini(self):
        from gemini_converter import DEFAULT_MODEL
        w, v = self.page("Gambar ke Markdown dengan Gemini", "AI membaca gambar dan susunan dokumen. Memerlukan internet dan Gemini API key.")
        self.gemini_list = DropList({".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}, multiple=False)
        v.addWidget(self.gemini_list, 1)
        v.addLayout(self.file_controls(self.gemini_list))
        form = QFormLayout()
        self.gemini_key = QLineEdit()
        self.gemini_key.setMinimumHeight(42)
        self.gemini_key.setEchoMode(QLineEdit.Password)
        self.gemini_key.setPlaceholderText("API key hanya untuk sesi ini; tidak disimpan ke file")
        self.gemini_model = QComboBox()
        self.gemini_model.setMinimumHeight(42)
        self.gemini_model.setEditable(True)
        self.gemini_model.addItems([DEFAULT_MODEL, "gemini-3.8-flash"])
        form.addRow("Gemini API key", self.gemini_key)
        form.addRow("Model", self.gemini_model)
        v.addLayout(form)
        link = QLabel('<a style="color:#00a987" href="https://aistudio.google.com/apikey">Login Google dan buat API key di Google AI Studio</a> · <a style="color:#00a987" href="https://ai.google.dev/gemini-api/docs/pricing">Kuota, biaya, dan ketentuan data</a>')
        link.setStyleSheet("QLabel a { color: #00a987; }")
        link.setOpenExternalLinks(True)
        link.setWordWrap(True)
        v.addWidget(link)
        hint = QLabel("Gratis mengikuti kuota akun/model; paket berbayar dapat dikenai biaya. Pada layanan gratis, Google dapat memakai konten untuk meningkatkan produk. Hasil AI tetap perlu diperiksa.")
        hint.setObjectName("muted"); hint.setWordWrap(True)
        v.addWidget(hint)
        self.gemini_consent = QCheckBox("Saya setuju gambar pilihan dikirim ke Google Gemini untuk konversi.")
        v.addWidget(self.gemini_consent)
        self.gemini_list.model().rowsInserted.connect(lambda *args: self.gemini_consent.setChecked(False))
        self.gemini_list.model().rowsRemoved.connect(lambda *args: self.gemini_consent.setChecked(False))
        self.gemini_button = QPushButton("Kirim ke Gemini dan simpan Markdown")
        self.gemini_button.setObjectName("primary")
        self.gemini_button.clicked.connect(lambda: self.convert_markdown("gemini"))
        v.addWidget(self.gemini_button)
        return w

    def image_source_key(self):
        files = self.image_markdown_list.paths()
        if len(files) != 1 or not files[0].exists():
            return None
        stat = files[0].stat()
        return (str(files[0].resolve()), stat.st_mtime_ns, stat.st_size)

    def update_ocr_region_label(self, *args):
        if self.image_source_key() != self.ocr_region_source:
            self.reset_ocr_regions()

    def reset_ocr_regions(self):
        self.ocr_regions = []
        self.ocr_region_source = None
        self.ocr_region_label.setText("Seluruh gambar")

    def choose_ocr_regions(self):
        files = self.image_markdown_list.paths()
        if len(files) != 1:
            return self.info("Tambahkan tepat satu gambar dahulu.", True)
        try:
            from ocr_regions import RegionDialog
            self.update_ocr_region_label()
            dialog = RegionDialog(files[0], self.ocr_regions, self)
            if dialog.exec():
                self.ocr_regions = dialog.canvas.regions
                self.ocr_region_source = self.image_source_key()
                self.ocr_region_label.setText(f"{len(self.ocr_regions)} area, sesuai urutan pilihan" if self.ocr_regions else "Seluruh gambar")
        except Exception as exc:
            self.info(f"Tidak dapat memilih area: {exc}", True)

    def convert_markdown(self, kind="pdf"):
        if not isinstance(kind, str):
            kind = "pdf"
        if self.markdown_process is not None:
            return
        if kind == "gemini":
            if not self.gemini_key.text().strip():
                return self.info("Masukkan API key Gemini dari Google AI Studio.", True)
            if not self.gemini_consent.isChecked():
                return self.info("Centang persetujuan pengiriman gambar ke Google dahulu.", True)
        files = (self.gemini_list if kind == "gemini" else self.image_markdown_list if kind == "image" else self.markdown_list).paths()
        if len(files) != 1:
            return self.info("Tambahkan tepat satu file untuk dikonversi ke Markdown.", True)
        source = files[0]
        target = self.output_path("Simpan Markdown", "Markdown (*.md)", source.with_suffix(".md").name)
        if target is None:
            return
        if target.suffix.lower() != ".md":
            target = target.with_name(target.name + ".md")
            if target.exists():
                return self.info("File hasil sudah ada. Pilih nama lain atau pilih file .md tersebut langsung.", True)
        if target.resolve() == source.resolve():
            return self.info("File hasil harus berbeda dari PDF sumber.", True)
        self.update_ocr_region_label()
        options = {"regions": self.ocr_regions, "layout": self.ocr_layout.currentData(), "split": self.ocr_split.value() / 100, "model": self.gemini_model.currentText().strip()}
        self.markdown_target = target
        process = QProcess(self)
        self.markdown_process = process
        self.markdown_button.setEnabled(False)
        self.image_markdown_button.setEnabled(False)
        self.gemini_button.setEnabled(False)
        self.markdown_button.setText("Sedang mengonversi…")
        self.status.setText(f"{'Gemini sedang memproses' if kind == 'gemini' else 'MarkItDown sedang memproses'}: {source.name}")
        if kind == "gemini":
            env = QProcessEnvironment.systemEnvironment()
            env.insert("ASNKIT_GEMINI_API_KEY", self.gemini_key.text().strip())
            process.setProcessEnvironment(env)
            self.gemini_consent.setChecked(False)
        process.finished.connect(self.markdown_finished)
        process.errorOccurred.connect(self.markdown_error)
        process.start(sys.executable, [str(Path(__file__).with_name("markdown_converter.py")), str(source), str(target), kind, self.ocr_language.currentData(), json.dumps(options)])

    def markdown_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.markdown_finished(-1, QProcess.ExitStatus.CrashExit)

    def markdown_finished(self, exit_code, exit_status):
        process = self.markdown_process
        if process is None:
            return
        error = bytes(process.readAllStandardError()).decode("utf-8", errors="replace").strip()
        self.markdown_process = None
        self.markdown_button.setEnabled(True)
        self.image_markdown_button.setEnabled(True)
        self.gemini_button.setEnabled(True)
        self.markdown_button.setText("Simpan sebagai Markdown")
        process.deleteLater()
        if exit_code != 0 or exit_status != QProcess.ExitStatus.NormalExit:
            self.info(f"Konversi Markdown gagal: {error[-2000:] or 'Proses tidak dapat diselesaikan.'}", True)
        else:
            self.info(f"Markdown berhasil disimpan: {self.markdown_target}")

    def closeEvent(self, event):
        if self.markdown_process is not None:
            QMessageBox.information(self, "Konversi berlangsung", "Tunggu konversi Markdown selesai sebelum menutup ASNkit.")
            event.ignore()
        else:
            super().closeEvent(event)

    def make_images(self):
        w, v = self.page("Jadikan gambar sebagai PDF", "Tambahkan satu atau beberapa gambar. Urutan daftar menjadi urutan halaman.")
        listing = DropList({".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"})
        v.addWidget(listing, 1)
        v.addLayout(self.file_controls(listing, "Tambah gambar"))
        row = QHBoxLayout(); row.addStretch()
        run = QPushButton("Buat PDF"); run.setObjectName("primary")
        run.clicked.connect(lambda: self.images_to_pdf(listing))
        row.addWidget(run); v.addLayout(row)
        return w

    def make_viewer(self):
        w, v = self.page("PDF Viewer", "Buka PDF untuk membaca halaman, mengatur zoom, dan berpindah halaman.")
        bar = QHBoxLayout()
        open_button = QPushButton("Buka PDF")
        self.viewer_page = QSpinBox()
        self.viewer_page.setMinimum(1)
        self.viewer_page.setEnabled(False)
        self.viewer_page.setPrefix("Halaman ")
        self.viewer_total = QLabel("/ 0")
        self.viewer_total.setObjectName("muted")
        self.viewer_zoom = QComboBox()
        self.viewer_zoom.addItems(["Lebar halaman", "Halaman penuh", "100%", "125%", "150%", "200%"])
        open_button.clicked.connect(self.open_viewer_pdf)
        self.viewer_page.valueChanged.connect(self.go_to_viewer_page)
        self.viewer_zoom.currentIndexChanged.connect(self.set_viewer_zoom)
        bar.addWidget(open_button)
        bar.addSpacing(10)
        bar.addWidget(self.viewer_page)
        bar.addWidget(self.viewer_total)
        bar.addStretch()
        bar.addWidget(QLabel("Zoom"))
        bar.addWidget(self.viewer_zoom)
        v.addLayout(bar)

        self.pdf_document = QPdfDocument(self)
        self.pdf_view = QPdfView()
        self.pdf_view.setDocument(self.pdf_document)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        self.pdf_view.pageNavigator().currentPageChanged.connect(self.sync_viewer_page)
        self.pdf_view.setStyleSheet("background: #111d24; border: 1px solid #38505a; border-radius: 8px;")
        v.addWidget(self.pdf_view, 1)
        return w

    def make_about(self):
        w, v = self.page("Tentang ASNkit", "Perangkat sederhana untuk membantu pekerjaan PDF sehari-hari.")
        details = QLabel(
            f"<h2>{APP_NAME} <span style='font-size:10pt'>v{APP_VERSION}</span></h2>"
            "<p>ASNkit adalah aplikasi desktop open source yang menyediakan alat untuk menggabungkan dan memisahkan PDF, "
            "mengubah dokumen, membuat PDF dari gambar, serta membaca PDF.</p>"
            "<p>Alat PDF dan OCR diproses lokal. Fitur Gemini bersifat opsional dan mengirim gambar ke Google setelah persetujuan. "
            "Kode sumbernya menggunakan lisensi <a href='https://opensource.org/license/mit/'>MIT</a>, sehingga dapat dipelajari "
            "dan dikembangkan kembali sesuai ketentuan lisensi.</p>"
            "<h3>Bantu ASNkit terus berkembang</h3>"
            "<p>Masukan, ide, dan kontribusi sangat berarti untuk menyempurnakan aplikasi ini. Jika ASNkit bermanfaat dan Anda ingin "
            f"ikut mendukung pengembangannya, boleh kasih cendol di <a href='{DONATION_URL}'>Trakteer @radarswingid</a>. "
            "Dukungan Anda membantu memberi waktu dan semangat untuk mengembangkan ASNkit.</p>"
        )
        details.setObjectName("aboutText")
        details.setTextFormat(Qt.RichText)
        details.setTextInteractionFlags(Qt.TextBrowserInteraction)
        details.setOpenExternalLinks(True)
        details.setWordWrap(True)
        details.setMaximumWidth(760)
        v.addWidget(details)
        v.addStretch()
        return w

    def open_viewer_pdf(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Buka PDF", "", "PDF (*.pdf)")
        if not filename:
            return
        load_error = self.pdf_document.load(filename)
        if load_error != QPdfDocument.Error.None_:
            self.info(f"Tidak dapat membuka PDF: {self.pdf_document.error()}", True)
            return
        count = self.pdf_document.pageCount()
        self.viewer_page.blockSignals(True)
        self.viewer_page.setRange(1, max(1, count))
        self.viewer_page.setValue(1)
        self.viewer_page.blockSignals(False)
        self.viewer_page.setEnabled(count > 0)
        self.viewer_total.setText(f"/ {count}")
        self.pdf_view.pageNavigator().jump(0, QPointF(0, 0))
        self.status.setText(f"Sedang melihat: {Path(filename).name}")

    def go_to_viewer_page(self, page_number):
        if self.pdf_document.pageCount():
            self.pdf_view.pageNavigator().jump(page_number - 1, QPointF(0, 0))

    def sync_viewer_page(self, page_index):
        self.viewer_page.blockSignals(True)
        self.viewer_page.setValue(page_index + 1)
        self.viewer_page.blockSignals(False)

    def set_viewer_zoom(self, index):
        if index == 0:
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        elif index == 1:
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)
        else:
            factor = [1.0, 1.25, 1.5, 2.0][index - 2]
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
            self.pdf_view.setZoomFactor(factor)

    def output_path(self, caption, filter_text, default):
        name, _ = QFileDialog.getSaveFileName(self, caption, str(Path.home() / default), filter_text)
        return Path(name) if name else None

    def info(self, message, error=False):
        self.status.setText(message)
        if error:
            QMessageBox.critical(self, "Proses gagal", message)
        else:
            QMessageBox.information(self, "Selesai", message)

    def combine(self, listing):
        files = listing.paths()
        if len(files) < 2:
            return self.info("Tambahkan setidaknya dua file PDF.", True)
        target = self.output_path("Simpan PDF gabungan", "PDF (*.pdf)", "gabungan.pdf")
        if not target: return
        try:
            from pypdf import PdfWriter
            writer = PdfWriter()
            for file in files: writer.append(str(file))
            with target.open("wb") as out: writer.write(out)
            writer.close()
            self.info(f"PDF berhasil digabungkan: {target}")
        except Exception as exc: self.info(f"Tidak dapat menggabungkan PDF: {exc}", True)

    def split(self, listing):
        files = listing.paths()
        if not files: return self.info("Tambahkan satu file PDF terlebih dahulu.", True)
        try:
            from pypdf import PdfReader, PdfWriter
            reader = PdfReader(str(files[0]))
            outdir = QFileDialog.getExistingDirectory(self, "Pilih folder hasil", str(files[0].parent))
            if not outdir: return
            if self.split_mode.currentIndex() == 0:
                for i, page in enumerate(reader.pages, 1):
                    writer = PdfWriter(); writer.add_page(page)
                    with open(Path(outdir) / f"{files[0].stem}_halaman_{i:03}.pdf", "wb") as out: writer.write(out)
            else:
                start, end = self.page_start.value(), self.page_end.value()
                if start > end or end > len(reader.pages):
                    return self.info(f"Rentang tidak valid. Dokumen berisi {len(reader.pages)} halaman.", True)
                writer = PdfWriter()
                for i in range(start - 1, end): writer.add_page(reader.pages[i])
                with open(Path(outdir) / f"{files[0].stem}_halaman_{start}-{end}.pdf", "wb") as out: writer.write(out)
            self.info(f"PDF selesai dipisahkan ke folder: {outdir}")
        except Exception as exc: self.info(f"Tidak dapat memisahkan PDF: {exc}", True)

    def convert_documents(self):
        files = self.convert_list.paths()
        if not files: return self.info("Tambahkan file yang akan dikonversi.", True)
        try:
            if self.conversion_mode.currentIndex() == 0:
                from pdf2docx import Converter
                for source in files:
                    target = self.output_path("Simpan dokumen Word", "Word (*.docx)", source.with_suffix(".docx").name)
                    if not target: return
                    converter = Converter(str(source))
                    try: converter.convert(str(target))
                    finally: converter.close()
            else:
                target_dir = QFileDialog.getExistingDirectory(self, "Pilih folder hasil PDF", str(files[0].parent))
                if not target_dir: return
                for source in files:
                    target = Path(target_dir) / source.with_suffix(".pdf").name
                    if target.exists():
                        raise RuntimeError(f"File sudah ada: {target}. Pilih folder lain agar file tidak tertimpa.")
                    with tempfile.TemporaryDirectory(prefix="asnkit-lo-") as profile:
                        result = subprocess.run([
                            "libreoffice", f"-env:UserInstallation={Path(profile).as_uri()}",
                            "--headless", "--convert-to", "pdf", "--outdir", target_dir,
                            str(source),
                        ], capture_output=True, text=True, timeout=120)
                        if result.returncode or not target.is_file():
                            raise RuntimeError(result.stderr or result.stdout or "LibreOffice gagal membuat PDF")
            self.info("Konversi dokumen selesai.")
        except Exception as exc:
            self.info(f"Konversi gagal: {exc}\nPDF ke Word membutuhkan pdf2docx. Word ke PDF membutuhkan LibreOffice.", True)

    def images_to_pdf(self, listing):
        files = listing.paths()
        if not files: return self.info("Tambahkan setidaknya satu gambar.", True)
        target = self.output_path("Simpan PDF", "PDF (*.pdf)", "gambar.pdf")
        if not target: return
        try:
            from PIL import Image
            pages = []
            for file in files:
                with Image.open(file) as im:
                    if im.mode in ("RGBA", "LA", "P"):
                        rgba = im.convert("RGBA")
                        background = Image.new("RGB", rgba.size, "white")
                        background.paste(rgba, mask=rgba.getchannel("A"))
                        pages.append(background)
                    else: pages.append(im.convert("RGB"))
            pages[0].save(target, "PDF", save_all=True, append_images=pages[1:])
            self.info(f"PDF berhasil dibuat: {target}")
        except Exception as exc: self.info(f"Tidak dapat membuat PDF dari gambar: {exc}", True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(Path(__file__).with_name("asnkit.svg"))))
    app.setDesktopFileName("ASNkit")
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")
    window = PdfToolkit()
    window.show()
    sys.exit(app.exec())
