# !/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QLabel, QApplication, QMainWindow
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import pyqtSlot

from modules.camera_views import MainWindowCamera
from modules.tools import abspath
from modules.analyzer import Analyser


def my_exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(r'data\ui\main_window.ui', self)
        self.camera = self.color_range_wind = None

        self.analyzer = Analyser(self)

        # Цвета, доступные для выбора
        self.colors = {}

        self.initUI()

    def initUI(self):
        # Включаем камеру
        self.camera = MainWindowCamera(self, self.MainVideoBox)
        self.camera.changePixmap.connect(self.setImage)
        self.camera.start()

        self.load_colors()

        # Добавляем действия для событий
        self.color_range_settings.triggered.connect(
            self.open_color_range_window)

        for i in [self.curr_color_1, self.curr_color_2]:
            # Если активировано выпадающее меню, то убираем выбранные цвета
            i.dropDownMenu.connect(self.update_colors_in_comboBox)

            # При выборе цвета загружаем его в систему распознавания
            i.currentTextChanged.connect(self.set_current_colors)

    def load_colors(self):
        # Загружаем данные из файла
        try:
            with open(abspath(r'data\settings\colors_settings.json'),
                      encoding='utf-8') as file:
                self.colors = {i['name']: [i['hsv_min'], i['hsv_max']]
                               for i in json.load(file)['Colors']}
        except Exception:
            pass

    def set_current_colors(self):
        # Устанавливаем выбранные цвета в распознавание камеры
        current_colors = {i: self.colors[i] for i in
                          map(lambda x: x.currentText(),
                              [self.curr_color_1, self.curr_color_2])
                          if i in self.colors}
        self.camera.set_current_colors(current_colors)
        self.analyzer.update_colors({
            num: {name: current_colors[name]}
            for num, name in enumerate(current_colors)})

    def update_colors_in_comboBox(self):
        # Предварительно отчищаем от всех значений
        self.sender().clear()

        # Получаем название объект, у которого сработал сигнал
        sender_name = self.sender().objectName()

        # Получаме название цвтеа из другого comboBox
        sec_col = getattr(
            self, str(list(filter(
                lambda x: x != sender_name,
                ['curr_color_1', 'curr_color_2']))[0])).currentText()

        # Устанавливаем все зачения, которые не выбраны в другом comboBox
        for i in filter(lambda x: x != sec_col, self.colors.keys()):
            self.sender().addItem(i)

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
