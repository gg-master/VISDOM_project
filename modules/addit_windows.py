from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QMessageBox, QComboBox
from PyQt5.QtGui import QImage, QPixmap, QCloseEvent
from PyQt5.QtCore import pyqtSlot
from modules.camera_views import ColorRangeCamera
# QComboBox.signalsBlocked()
import json


class ColorRangeWindow(QWidget):
    def __init__(self, parent, *args, **kwargs):
        super().__init__()
        uic.loadUi(r'data\ui\color_range_settings_window.ui', self)
        self.parent = parent
        self.camera = self.colors = None
        self.saved = False
        self.initUI()

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.VideoBox.setPixmap(QPixmap.fromImage(image))

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

        # При выборе другого элемента проверяем на изменение текущего
        # self.colorsBox.activated[str].connect(self.color_changed_event)

        self.colorsBox.view().pressed.connect(self.color_changed_event)
        print(dir(self.colorsBox.view()))
        self.add_new_color_btn.clicked.connect(self.create_new_color)

        # Загружаем все цвета из файла
        self.load_colors()
        # self.colorsBox.blockSignals(True)

    def load_colors(self):
        # Загружаем данные из файла
        with open(r'data\settings\colors_settings.json',
                  encoding='utf-8') as file:
            self.colors = {i['name']: [i['hsv_min'], i['hsv_max']]
                           for i in json.load(file)['Colors']}

        # Закражаем названия цветов в comboBox
        for i in self.colors.keys():
            self.colorsBox.addItem(i)

        # Устанавливаем выбранный элемент как последний выбранный
        self.colorsBox.setProperty('lastitem', self.colorsBox.currentText())

        # Устанавливаем значения цветов
        self.set_color_val()

    def set_color_val(self, *args, default=False):
        # Дефолтное значение для нового цвета
        if default:
            color = [[0, 0, 0], [255, 255, 255]]
        else:
            color = self.colors[self.colorsBox.currentText()]

        # Перебирая слайдеры и лэйблы устаналиваем соотвествующие значения
        for n, (slider, label) in enumerate(
                zip([self.st_hue_slider, self.st_sat_slider,
                     self.st_val_slider],
                    [self.st_hue_val, self.st_sat_val, self.st_val_val])):
            slider.setValue(color[0][n])
            label.setText(str(color[0][n]))
        for n, (slider, label) in enumerate(
                zip([self.end_hue_slider, self.end_sat_slider,
                     self.end_val_slider],
                    [self.end_hue_val, self.end_sat_val, self.end_val_val])):
            slider.setValue(color[1][n])
            label.setText(str(color[1][n]))

    def get_hsv_min_max(self):
        return [
            [self.st_hue_slider.value(), self.st_sat_slider.value(),
             self.st_val_slider.value()],
            [self.end_hue_slider.value(),
             self.end_sat_slider.value(),
             self.end_val_slider.value()]
        ]

    def set_camera_hsv_colors(self):
        self.camera.set_hmin_hmax(*self.get_hsv_min_max())

    def is_color_edited(self, name=None) -> bool:
        hsv_min_max = self.get_hsv_min_max()
        name = self.colorsBox.currentText() if name is None else name
        print(name)
        print(hsv_min_max)
        print(self.colors[name] if name in self.colors else [])
        if name not in self.colors or self.colors[name] != hsv_min_max:
            self.saved = False if self.saved is not None else None
            return True
        self.saved = True
        return False

    def quest_box(self):
        # Окно с подтвердением
        msg = QMessageBox()
        ret = msg.question(self, 'Имеются несохраненные изменения',
                           "Действительно продолжить без сохранения?\n"
                           "Все изменения будут утеряны.",
                           msg.Yes | msg.No)
        if ret == msg.Yes:
            # Выход без сохранения
            self.saved = True
        else:
            self.saved = None

    def save_edited_color(self):
        # Сохраниение измененного цвета
        hsv_min_max = self.get_hsv_min_max()
        name = self.colorsBox.currentText()
        self.colors[name] = hsv_min_max

    def save_colors_to_json(self):
        # Сохранение все цветов в файл
        with open(r'data\settings\colors_settings.json', 'w',
                  encoding='utf-8') as file:
            json.dump({'Colors': [{'name': k,
                                   'hsv_min': v[0], 'hsv_max': v[1]}
                                  for k, v in self.colors]}, file)

    def create_new_color(self):
        # При создании нового цвета проверяем имеются ли несохраненные данные
        if self.is_color_edited():
            self.quest_box()
        else:
            name = 'Цвет№_0'
            if name in self.colors:
                name = "Цвет№_" + str(sorted(map(
                    lambda x: int(x.split('_')[-1]),
                    filter(lambda x: 'Цвет№_' in x, self.colors.keys())))[
                                          -1] + 1)
            print(name)
            self.colorsBox.addItem(name)
            self.colorsBox.setCurrentText(name)
            self.set_color_val(default=True)

    def color_changed_event(self, index):
        item = self.colorsBox.model().itemFromIndex(index)
        print(item.text())
        # new_item = self.colorsBox.currentText()
        # last_item = self.colorsBox.property('lastitem')
        # if last_item == new_item:
        #     return
        #
        # print(last_item, '->', new_item)
        #
        # # При переключении цвета проверяем имеются ли несохраненные изменения
        # if self.is_color_edited(name=last_item):
        #     if self.saved is not None:
        #         self.quest_box()
        #     elif self.saved is None:
        #         self.saved = False
        #
        # if self.saved is not None and self.saved:
        #     self.colorsBox.setProperty('lastitem', new_item)
        #
        # print(self.saved)
        # if self.saved:
        #     self.set_color_val()
        # elif self.saved is None or not self.saved:
        #     self.colorsBox.setCurrentText(last_item)

    def sliderChanged(self):
        sname = self.sender().objectName()
        getattr(self, f"{sname[:sname.rfind('_')]}_val").setText(
            str(self.sender().value()))
        self.set_camera_hsv_colors()

    def closeEvent(self, a0: QCloseEvent) -> None:
        # TODO Обработка добавленных элементов и их сохранение в json файле
        super().closeEvent(a0)
