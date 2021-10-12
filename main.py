# !/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json

from PyQt5 import uic, QtGui
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow

from modules.tools import abspath
from modules.analyzer import Analyzer
from modules.camera_views import MainWindowCamera


def my_exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(abspath(r'data\ui\main_window.ui'), self)
        self.camera = self.color_range_wind = \
            self.graph_window = self.an_gr_set = None

        self.analyzer = Analyzer(self)
        self.analyzer.newCoordinatesSignal.connect(self.set_coord_in_label)

        # Цвета, доступные для выбора
        self.colors = {}

        self.initUI()

    def initUI(self):
        # Включаем камеру
        self.camera = MainWindowCamera(self, self.MainVideoBox)
        self.camera.changePixmap.connect(self.setImage)
        self.camera.start()

        self.load_colors()

        self.load_breath_set()
        self.set_breath_sett()

        # Добавляем действия для событий
        self.color_range_settings.triggered.connect(
            self.open_color_range_window)

        self.open_graph_inWindow.triggered.connect(
            self.open_graph_in_window)

        self.analyzer_graph_settings.triggered.connect(
            self.open_analyzer_graph_settings_window)

        for i in [self.curr_color_1, self.curr_color_2]:
            # Если активировано выпадающее меню, то убираем выбранные цвета
            i.dropDownMenu.connect(self.update_colors_in_comboBox)

            # При выборе цвета загружаем его в систему распознавания
            i.currentTextChanged.connect(self.set_current_colors)

        for i in [self.timeDelta, self.minDeltaTop, self.maxDeltaTop,
                  self.minDeltaBot, self.maxDeltaBot]:
            i.valueChanged.connect(self.set_breath_sett)

    def load_breath_set(self):
        # Загружаем и устанавливаем все значения для дыхания из файла
        try:
            with open(abspath(r'data\settings\breath_rec_settings.json'),
                      encoding='utf-8') as file:
                dct = json.load(file)
                self.timeDelta.setValue(dct['TimeDelta'])
                self.minDeltaTop.setValue(dct['MinDeltaTop'])
                self.maxDeltaTop.setValue(dct['MaxDeltaTop'])
                self.minDeltaBot.setValue(dct['MinDeltaBot'])
                self.maxDeltaBot.setValue(dct['MaxDeltaBot'])
        except Exception:
            pass

    def load_colors(self):
        # Загружаем данные из файла
        try:
            with open(abspath(r'data\settings\colors_settings.json'),
                      encoding='utf-8') as file:
                self.colors = {i['name']: [i['hsv_min'], i['hsv_max']]
                               for i in json.load(file)['Colors']}
        except Exception:
            pass

    def set_breath_sett(self):
        # Получаем значения для анализа из окна
        self.analyzer.set_new_settings(
            timeDelta=self.timeDelta.value(),
            delta_top=[self.minDeltaTop.value(), self.maxDeltaTop.value()],
            delta_bot=[self.minDeltaBot.value(), self.maxDeltaBot.value()])

    def set_current_colors(self):
        # Устанавливаем выбранные цвета в распознавание камеры
        current_colors = {i: self.colors[i] for i in
                          map(lambda x: x.currentText(),
                              [self.curr_color_1, self.curr_color_2])
                          if i in self.colors}
        self.analyzer.update_colors(
            {n: {'name': i if i else None} for n, i in enumerate(
                map(lambda x: x.currentText(),
                    [self.curr_color_1, self.curr_color_2]), start=1)})

        self.camera.set_current_colors(current_colors)

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

    def set_coord_in_label(self):
        # Получаем последние координаты и устанавливаем их в лэйблы
        y1, y2, x1, x2 = map(lambda x: str(int(x)),
                             self.analyzer.get_last_coordinates())
        self.val_x1.setText(x1)
        self.val_x2.setText(x2)
        self.val_y1.setText(y1)
        self.val_y2.setText(y2)

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.MainVideoBox.setPixmap(QPixmap.fromImage(image))

    def open_color_range_window(self):
        # Открываем окно для настройки цветов
        from modules.addit_windows import ColorRangeWindow
        self.color_range_wind = ColorRangeWindow(self)
        self.color_range_wind.show()

    def open_graph_in_window(self):
        from modules.addit_windows import GraphWindow
        self.graph_window = GraphWindow(self)
        self.graph_window.show()

    def open_analyzer_graph_settings_window(self):
        from modules.addit_windows import AnalyzerGraphSettingsWindow
        self.an_gr_set = AnalyzerGraphSettingsWindow(self)
        self.an_gr_set.show()

    def save_breath_sett_to_json(self):
        # Сохраняем все настройки в файл
        try:
            with open(abspath(r'data\settings\breath_rec_settings.json'), 'w',
                      encoding='utf-8') as file:
                json.dump({
                    "TimeDelta": self.timeDelta.value(),
                    "MinDeltaTop": self.minDeltaTop.value(),
                    "MaxDeltaTop": self.maxDeltaTop.value(),
                    "MinDeltaBot": self.minDeltaBot.value(),
                    "MaxDeltaBot": self.maxDeltaBot.value()}, file,
                    ensure_ascii=False)
        except Exception as e:
            print(e)
            pass

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.save_breath_sett_to_json()
        super().closeEvent(a0)


if __name__ == '__main__':
    sys.excepthook = my_exception_hook

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
