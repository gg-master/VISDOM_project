import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QLabel, QApplication, QMainWindow
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import pyqtSlot
from modules.camera_views import MainWindowCamera


def my_exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    # sys._excepthook(exctype, value, traceback)
    sys.exit(1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(r'data\ui\main_window.ui', self)
        self.initUI()

    def initUI(self):
        # Включаем камеру
        self.camera = MainWindowCamera(self, self.MainVideoBox)
        self.camera.changePixmap.connect(self.setImage)
        self.camera.start()
        # Добавляем действия для событий
        self.color_range_settings.triggered.connect(
            self.open_color_range_window)

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.MainVideoBox.setPixmap(QPixmap.fromImage(image))

    def open_color_range_window(self):
        # Открываем окно для настройки цветов
        from modules.addit_windows import ColorRangeWindow
        self.color_range_wind = ColorRangeWindow(self)
        self.color_range_wind.show()

if __name__ == '__main__':
    sys.excepthook = my_exception_hook

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
