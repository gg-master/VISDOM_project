from PyQt5.Qt import *
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtCore import pyqtSignal, QEvent


class ComboBoxPDrDwSi(QComboBox):
    dropDownMenu = pyqtSignal()

    def __init__(self, parent=None):
        QComboBox.__init__(self, parent)
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            mouse_event = QMouseEvent(event)
            if mouse_event.buttons() == Qt.LeftButton:
                self.dropDownMenu.emit()
                return super().eventFilter(obj, event)
        return False
