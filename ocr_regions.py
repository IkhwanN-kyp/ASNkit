"""Select ordered OCR regions without changing the source image."""
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QImageReader, QPainter, QPen
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget


class RegionCanvas(QWidget):
    def __init__(self, source, regions=None):
        super().__init__()
        reader = QImageReader(str(source))
        reader.setAutoTransform(True)
        self.image = reader.read()
        if self.image.isNull():
            raise ValueError("Gambar tidak dapat dibuka untuk pemilihan area.")
        self.regions = list(regions or [])
        self.start = self.end = None
        self.setMinimumSize(320, 300)
        self.setCursor(Qt.CrossCursor)

    def image_rect(self):
        size = self.image.size().scaled(self.size(), Qt.KeepAspectRatio)
        return QRectF((self.width()-size.width())/2, (self.height()-size.height())/2, size.width(), size.height())

    def normal(self, point):
        box = self.image_rect()
        return (max(0., min(1., (point.x()-box.x())/box.width())),
                max(0., min(1., (point.y()-box.y())/box.height())))

    def selection(self):
        if self.start is None or self.end is None:
            return None
        x1,y1 = self.normal(self.start); x2,y2 = self.normal(self.end)
        return [min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2)]

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.image_rect().contains(event.position()):
            self.start = self.end = event.position()
            self.update()

    def mouseMoveEvent(self, event):
        if self.start is not None:
            self.end = event.position()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.start is not None:
            self.end = event.position()
            region = self.selection()
            if region[2]-region[0] >= .01 and region[3]-region[1] >= .01 and len(self.regions) < 30:
                self.regions.append(region)
            self.start = self.end = None
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('#101820'))
        box = self.image_rect()
        painter.drawImage(box, self.image)
        painter.setPen(QPen(QColor('#00d4aa'), 2))
        for index, (x1,y1,x2,y2) in enumerate(self.regions + ([self.selection()] if self.start is not None else []), 1):
            rect = QRectF(box.x()+x1*box.width(), box.y()+y1*box.height(), (x2-x1)*box.width(), (y2-y1)*box.height())
            painter.fillRect(rect, QColor(0,212,170,30))
            painter.drawRect(rect)
            painter.fillRect(QRectF(rect.x(),rect.y(),24,24), QColor('#101820'))
            painter.drawText(QRectF(rect.x(),rect.y(),24,24), Qt.AlignCenter, str(index))


class RegionDialog(QDialog):
    def __init__(self, source, regions=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pilih area baca OCR")
        self.resize(850,850)
        layout = QVBoxLayout(self)
        hint = QLabel("Seret kotak sesuai urutan baca: judul, kolom kiri, lalu kolom kanan. Hindari ilustrasi dan halaman sebelah. Anda dapat memilih beberapa blok teks secara terpisah.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.canvas = RegionCanvas(source, regions)
        layout.addWidget(self.canvas,1)
        row = QHBoxLayout()
        undo = QPushButton("Batalkan area terakhir")
        undo.clicked.connect(self.undo)
        clear = QPushButton("Hapus semua area")
        clear.clicked.connect(self.clear)
        row.addWidget(undo);row.addWidget(clear);row.addStretch()
        layout.addLayout(row)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def undo(self):
        if self.canvas.regions:
            self.canvas.regions.pop();self.canvas.update()

    def clear(self):
        self.canvas.regions.clear();self.canvas.update()
