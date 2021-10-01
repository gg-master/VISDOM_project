from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QMessageBox, QComboBox
from PyQt5.QtGui import QImage, QPixmap, QCloseEvent
from PyQt5.QtCore import pyqtSlot, Qt
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

        # При переключении цвета загружаем данные о цвете
        self.colorsBox.activated[str].connect(self.color_changed_action)

        # Реагируем на событие раскрытия comboBox.
        self.colorsBox.dropDownMenu.connect(self.colBox_drop_down_action)
        self.colorsBox.editTextChanged.connect(self.editText_action)

        self.add_new_color_btn.clicked.connect(self.create_new_color)

        self.delete_color_btn.clicked.connect(self.delete_cur_color)

        self.confirm_btn.clicked.connect(self.save_edited_color)
        self.cancel_btn.clicked.connect(self.closeEvent)

        # Загружаем все цвета из файла
        self.load_colors()

    def load_colors(self):
        # Загружаем данные из файла
        try:
            with open(r'data\settings\colors_settings.json',
                      encoding='utf-8') as file:
                self.colors = {i['name']: [i['hsv_min'], i['hsv_max']]
                               for i in json.load(file)['Colors']}
        except Exception:
            self.colors = {'Цвет№_0': [[0, 0, 0], [255, 255, 255]]}
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
            cur_col = self.colorsBox.currentText()
            if cur_col not in self.colors:
                return
            color = self.colors[cur_col]

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

    def is_color_edited(self) -> bool:
        # Получаем название цвета и его сохраненное значание
        name = self.colorsBox.currentText()
        hsv_min_max = self.get_hsv_min_max()

        # Если подобного цвета нет или значения цвета отредактированы,
        # то считаем что цвет изменен
        if name not in self.colors or self.colors[name] != hsv_min_max:
            self.saved = False
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

    def save_edited_color(self):
        # Сохраниение измененного цвета
        hsv_min_max = self.get_hsv_min_max()
        name = self.colorsBox.currentText()
        orig_name = self.colorsBox.itemData(
            self.colorsBox.currentIndex(), Qt.UserRole)
        if name in self.colors:
            return
        if orig_name in self.colors:
            self.colors.pop(orig_name)
        self.colors[name] = hsv_min_max

    def save_colors_to_json(self):
        # Сохранение всех цветов в файл
        with open(r'data\settings\colors_settings.json', 'w',
                  encoding='utf-8') as file:
            # Загружаем все цвета в json файл
            json.dump({'Colors': [{'name': k,
                               'hsv_min': v[0], 'hsv_max': v[1]}
                              for k, v in self.colors.items()]}, file,
                      ensure_ascii=False)

    def remove_undetected_cur_item(self):
        # Если новый созданный элемент не был сохранен, то удаляем из списка
        index = self.colorsBox.currentIndex()
        if self.colorsBox.currentText() not in self.colors:
            # Также проверяем и по оригинальному имени
            orig_name = self.colorsBox.itemData(index, Qt.UserRole)
            if orig_name not in self.colors:
                self.colorsBox.removeItem(self.colorsBox.findText(
                    self.colorsBox.currentText()))
            else:
                self.colorsBox.model().item(index).setText(orig_name)

    def delete_cur_color(self):
        # Окно с подтвердением
        msg = QMessageBox()
        ret = msg.question(self, 'Удаление элемента',
                           "Действительно удалить элемент?\n"
                           "Это действие нельзя отменить.",
                           msg.Yes | msg.No)
        if ret == msg.Yes:
            # Удаляем выбранный элемент
            name_item = self.colorsBox.currentText()
            self.colorsBox.removeItem(self.colorsBox.findText(name_item))
            if name_item in self.colors:
                self.colors.pop(name_item)

        # Устанавливаем значения нового выбранного цвета
        self.set_color_val()

    def create_new_color(self):
        # При создании нового цвета проверяем имеются ли несохраненные данные
        if self.is_color_edited():
            self.quest_box()

        if self.saved:
            # Удаляем элемент, если не был сохранен
            self.remove_undetected_cur_item()

            # Создаем новый цвет
            name = 'Цвет№'
            if any(map(lambda x: name in x, self.colors.keys())):
                name = "Цвет№_" + str(sorted(map(
                    lambda x: abs(int(x.split('_')[-1])),
                    filter(lambda x: 'Цвет№_' in x, self.colors.keys())))[
                                          -1] + 1)
            # Помещаем новый цвет на первое место в списке
            self.colorsBox.insertItem(0, name)
            # Выбираем новый цвет
            self.colorsBox.setCurrentIndex(0)
            # Сбрасываем на дэфолтные значения диапазоны HSV
            self.set_color_val(default=True)

    def set_colBoxEnabled(self, flag):
        # Перебираем все элементы comboBox и устанавливаем им flag
        # как значение доступности
        color = None
        for i in range(self.colorsBox.count()):
            if self.colorsBox.itemText(i) in self.colors:
                self.colorsBox.model().item(i).setEnabled(flag)
            elif color is None:
                color = self.colorsBox.itemText(i)

        # Обрабатываем случай с автоматическим изменением названия элемента
        if color is not None:
            self.colorsBox.setCurrentText(color)

    def editText_action(self, text):
        # Устанавливаем текст из current элемента в список QComboBox
        # Получение индекса current элемента
        index = self.colorsBox.currentIndex()

        # По индексе определяем нужный элемент и изменяем его имя в списке
        self.colorsBox.model().item(index).setText(text)

        # Сохраняем оригинальное имя
        if self.colorsBox.itemData(index, Qt.UserRole) is None:
            text = self.colorsBox.itemText(index)
            self.colorsBox.setItemData(index, text, Qt.UserRole)

    def colBox_drop_down_action(self):
        # При раскрытии списка узнаем был ли редактировн цвет
        if self.is_color_edited():
            # Если был редактирован, то предупреждаем пользователя
            self.set_colBoxEnabled(False)
            self.quest_box()
        # Если же цвет сохранен, то мы можем переключаться между
        # другими цветами
        if self.saved:
            # Если элемент не найден в списке сохраненных цветов - удаляем
            self.remove_undetected_cur_item()

            self.set_color_val()
            self.set_colBoxEnabled(True)

    def color_changed_action(self, new_item):
        # При изменении выбранного цвета проверяем, чтобы предыдущий и
        # выбранный цвет не совпадали
        last_item = self.colorsBox.property('lastitem')
        self.colorsBox.setProperty('lastitem', new_item)

        if last_item == new_item:
            # Если элементы совпали, то выходим
            return
        # print(last_item, '->', new_item)

        # Переключаем цвет
        self.set_color_val()

    def sliderChanged(self):
        sname = self.sender().objectName()
        getattr(self, f"{sname[:sname.rfind('_')]}_val").setText(
            str(self.sender().value()))
        self.set_camera_hsv_colors()

    def closeEvent(self, a0: QCloseEvent = None) -> None:
        self.save_colors_to_json()
        super().close()
