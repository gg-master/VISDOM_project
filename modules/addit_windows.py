from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPixmap, QCloseEvent
from PyQt5.QtCore import pyqtSlot
from modules.camera_views import ColorRangeCamera


class ColorRangeWindow(QWidget):
    def __init__(self, parent, *args, **kwargs):
        super().__init__()
        uic.loadUi(r'data\ui\color_range_settings_window.ui', self)
        self.parent = parent
        self.initUI()

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.VideoBox.setPixmap(QPixmap.fromImage(image))

    def initUI(self):
        self.camera = ColorRangeCamera(self.parent, self.VideoBox)
        self.camera.changePixmap.connect(self.setImage)
        self.camera.start()

    def closeEvent(self, a0: QCloseEvent) -> None:
        super().closeEvent(a0)
