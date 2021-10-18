from PyQt5 import QtGui
from PyQt5.Qt import *
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtCore import pyqtSignal, QEvent


class ComboBoxPDrDwSi(QComboBox):
    # Комбо бокс с событием о раскрывании списка
    dropDownMenu = pyqtSignal()

    def __init__(self, parent=None):
        QComboBox.__init__(self, parent)
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        # Обрабатываем события
        if event.type() == QEvent.MouseButtonPress:
            mouse_event = QMouseEvent(event)

            # Если обнаружили клик мышью по выпадающему списку,
            # активируем сигнал
            if mouse_event.buttons() == Qt.LeftButton:
                self.dropDownMenu.emit()
                return super().eventFilter(obj, event)
        return False


class AutoClosedQWidget(QWidget):
    closeWindowSignal = pyqtSignal()

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.parent.closeWindowSignal.connect(self.close)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        # Отключаемся от родителя
        self.parent.closeWindowSignal.disconnect(self.close)

        # При закрытии сигнализируем всем дочерним окнам
        self.closeWindowSignal.emit()

        super().closeEvent(a0)
