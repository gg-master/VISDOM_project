from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPixmap, QCloseEvent
from PyQt5.QtCore import pyqtSlot
from modules.camera_views import ColorRangeCamera

import json


class ColorRangeWindow(QWidget):
    def __init__(self, parent, *args, **kwargs):
        super().__init__()
        uic.loadUi(r'data\ui\color_range_settings_window.ui', self)
        self.parent = parent
        self.camera = self.colors = None
        self.initUI()

    def initUI(self):
        # Инициализация камеры
        self.camera = ColorRangeCamera(self.parent, self.VideoBox)
        self.camera.changePixmap.connect(self.setImage)
        self.camera.start()

        # Подвязываем слайдеры к интерфейсу
        for i in [self.st_hue_slider, self.st_sat_slider, self.st_val_slider,
                  self.end_hue_slider, self.end_sat_slider,
                  self.end_val_slider]:
            i.valueChanged.connect(self.sliderChanged)

        self.colorsBox.currentIndexChanged.connect(self.color_index_changed)
        # Загружаем все цвета из файла
        self.load_colors()

    def load_colors(self):
        with open(r'data\settings\colors_settings.json',
                  encoding='utf-8') as file:
            self.colors = {i['name']: [i['hsv_min'], i['hsv_max']]
                           for i in json.load(file)['Colors']}
        for i in self.colors.keys():
            self.colorsBox.addItem(i)

        self.set_color_val()

    def set_color_val(self):
        color = self.colors[self.colorsBox.currentText()]
        for n, i in enumerate([self.st_hue_slider, self.st_sat_slider,
                               self.st_val_slider]):
            i.setValue(color[0][n])
        for n, i in enumerate([self.st_hue_val, self.st_sat_val,
                               self.st_val_val]):
            i.setText(str(color[0][n]))

        for n, i in enumerate([self.end_hue_slider, self.end_sat_slider,
                               self.end_val_slider]):
            i.setValue(color[1][n])
        for n, i in enumerate([self.end_hue_val, self.end_sat_val,
                               self.end_val_val]):
            i.setText(str(color[1][n]))

    def set_camera_hsv_colors(self, default=False):
        if default:
            self.camera.set_hmin_hmax((0, 0, 0), (255, 255, 255))
            return
        self.camera.set_hmin_hmax(
            (self.st_hue_slider.value(), self.st_sat_slider.value(),
             self.st_val_slider.value()),
            (self.end_hue_slider.value(), self.end_sat_slider.value(),
             self.end_val_slider.value())
        )

    def check_color_changed(self) -> bool:
        pass

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.VideoBox.setPixmap(QPixmap.fromImage(image))

    def color_index_changed(self):
        # TODO проверка был ли изменен цвет. И если изменен, то необходимо
        #  предупредить об это пользователя
        self.set_color_val()

    def sliderChanged(self):
        sname = self.sender().objectName()
        getattr(self, f"{sname[:sname.rfind('_')]}_val").setText(
            str(self.sender().value()))
        self.set_camera_hsv_colors()

    def closeEvent(self, a0: QCloseEvent) -> None:
        # TODO Обработка добавленных элементов и их сохранение в json файле
        super().closeEvent(a0)
