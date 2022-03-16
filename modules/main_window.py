import json

from PyQt5 import QtGui, uic
from PyQt5.QtCore import QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QMainWindow

from modules.analyzer import Analyzer
from modules.camera_views import Camera, MainWindowCamera
from modules.tools import abspath


class MainWindow(QMainWindow):
    closeWindowSignal = pyqtSignal()

    def __init__(self, camera, network):
        super().__init__()
        uic.loadUi(abspath('data/ui/main_window.ui'), self)

        self.cam_obj: Camera = camera
        self.network = network

        self.camera = self.color_range_wind = \
            self.graph_window = self.an_gr_set = \
            self.server_set = self.breath_logs_win = None

        self.analyzer = Analyzer(self)
        self.analyzer.newCoordinatesSignal.connect(self.set_coord_in_label)

        # Цвета, доступные для выбора
        self.colors = {}

        # Словарь со всеми вдохами за время работы программы
        self.signals_logs = {}

        self.initUI()

        # Таймер обновления состояния о подключении к серверу
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_network_state)
        self.timer.start(2000)

        # Первичная проверка состояния
        self.check_network_state()

    def initUI(self) -> None:
        # Включаем камеру
        self.start_cam()

        # Загружаем сохраненные цвета
        self.load_colors()

        # Загружаем настройки дыхания
        self.load_breath_set()
        self.set_breath_sett()

        # Добавляем действия для событий
        # Открытие различных окон
        self.color_range_settings.triggered.connect(
            self.open_color_range_window)
        self.open_graph_inWindow.triggered.connect(
            self.open_graph_in_window)
        self.analyzer_graph_settings.triggered.connect(
            self.open_analyzer_graph_settings_window)
        self.restart_camera.triggered.connect(self.restart_cam)
        self.server_settings.triggered.connect(self.open_server_sett_window)
        self.open_logs_breath.triggered.connect(self.open_breath_logs_window)

        # Изменение настроек в главном окне
        for i in [self.curr_color_1, self.curr_color_2]:
            # Если активировано выпадающее меню, то убираем выбранные цвета
            i.dropDownMenu.connect(self.update_colors_in_comboBox)

            # При выборе цвета загружаем его в систему распознавания
            i.currentTextChanged.connect(self.set_current_colors)

        for i in [self.timeDelta, self.minDeltaTop, self.maxDeltaTop,
                  self.minDeltaBot, self.maxDeltaBot]:
            i.valueChanged.connect(self.set_breath_sett)

    def start_cam(self):
        if self.camera is None:
            self.camera = MainWindowCamera(self.MainVideoBox, self.cam_obj)
            self.camera.changePixmap.connect(self.setImage)
        self.camera.start()

    def restart_cam(self) -> None:
        self.cam_obj.restart()
        self.camera.restart()

    def load_breath_set(self) -> None:
        # Загружаем и устанавливаем все значения для дыхания из файла
        try:
            with open(abspath('data/settings/breath_rec_settings.json'),
                      encoding='utf-8') as file:
                dct = json.load(file)
                self.timeDelta.setValue(dct['TimeDelta'])
                self.minDeltaTop.setValue(dct['MinDeltaTop'])
                self.maxDeltaTop.setValue(dct['MaxDeltaTop'])
                self.minDeltaBot.setValue(dct['MinDeltaBot'])
                self.maxDeltaBot.setValue(dct['MaxDeltaBot'])

                self.set_analyzer_graph_settings(dct['DetailSettings'])
        except FileNotFoundError:
            pass

    def load_colors(self) -> None:
        # Загружаем данные из файла
        try:
            with open(abspath('data/settings/colors_settings.json'),
                      encoding='utf-8') as file:
                self.colors = {i['name']: [i['hsv_min'], i['hsv_max']]
                               for i in json.load(file)['Colors']}
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def set_analyzer_graph_settings(self, data: dict) -> None:
        # Изменяем найтройки анализатора
        self.analyzer.set_new_settings(**data)

    def set_breath_sett(self) -> None:
        # Получаем значения для анализа из окна
        self.analyzer.set_new_settings(
            timeDelta=self.timeDelta.value(),
            delta_top=[self.minDeltaTop.value(), self.maxDeltaTop.value()],
            delta_bot=[self.minDeltaBot.value(), self.maxDeltaBot.value()])

    def drop_curr_col(self):
        for i in [self.curr_color_1, self.curr_color_2]:
            i.currentTextChanged.emit('Выберите цвет')

    def set_current_colors(self) -> None:
        # Устанавливаем выбранные цвета в распознавание камеры
        current_colors = {i: self.colors[i] for i in
                          map(lambda x: x.currentText(),
                              [self.curr_color_1, self.curr_color_2])
                          if i in self.colors}
        self.analyzer.update_colors(
            {n: {'name': i if i and i != 'Выберите цвет' else None}
             for n, i in enumerate(
                map(lambda x: x.currentText(),
                    [self.curr_color_1, self.curr_color_2]), start=1)})

        self.camera.set_current_colors(current_colors)

    def update_colors_in_comboBox(self) -> None:
        # # Предварительно отчищаем от всех значений
        self.sender().clear()

        # Получаем название объект, у которого сработал сигнал
        sender_name = self.sender().objectName()

        # Получаме название цвтеа из другого comboBox
        sec_col = getattr(
            self, str(list(filter(
                lambda x: x != sender_name,
                ['curr_color_1', 'curr_color_2']))[0])).currentText()

        # Сперва добавляем дефолтное значение
        self.sender().addItem('Выберите цвет')

        # Устанавливаем все зачения, которые не выбраны в другом comboBox
        for i in filter(lambda x: x != sec_col, self.colors.keys()):
            self.sender().addItem(i)

    def set_coord_in_label(self) -> None:
        # Получаем последние координаты и устанавливаем их в лэйблы
        y1, y2, x1, x2 = map(lambda x: str(int(x)),
                             self.analyzer.get_last_coordinates())
        self.val_x1.setText(x1)
        self.val_x2.setText(x2)
        self.val_y1.setText(y1)
        self.val_y2.setText(y2)

    @pyqtSlot(QImage)
    def setImage(self, image: QImage) -> None:
        self.MainVideoBox.setPixmap(QPixmap.fromImage(image))

    def close_extra_win(self):
        self.drop_curr_col()
        self.camera.stop()
        self.closeWindowSignal.emit()

    def open_color_range_window(self) -> None:
        # Закрываем окна для оптимизации
        self.close_extra_win()

        # Открываем окно для настройки цветов
        from modules.addit_windows import ColorRangeWindow
        self.color_range_wind = ColorRangeWindow(self)
        self.color_range_wind.show()

    def open_graph_in_window(self) -> None:
        from modules.addit_windows import GraphWindow
        self.graph_window = GraphWindow(self)
        self.graph_window.show()

    def open_analyzer_graph_settings_window(self) -> None:
        from modules.addit_windows import AnalyzerGraphSettingsWindow
        self.an_gr_set = AnalyzerGraphSettingsWindow(self)
        self.an_gr_set.show()

    def open_server_sett_window(self) -> None:
        from modules.addit_windows import ServerSettingsWindow
        self.server_set = ServerSettingsWindow(self, self.network)
        self.server_set.show()

    def open_breath_logs_window(self) -> None:
        from modules.addit_windows import BreathLogsWindow
        self.breath_logs_win = BreathLogsWindow(self)
        self.breath_logs_win.show()

    def save_breath_sett_to_json(self) -> None:
        # Сохраняем все настройки в файл
        try:
            with open(abspath('data/settings/breath_rec_settings.json'), 'w',
                      encoding='utf-8') as file:
                json.dump({
                    "TimeDelta": self.timeDelta.value(),
                    "MinDeltaTop": self.minDeltaTop.value(),
                    "MaxDeltaTop": self.maxDeltaTop.value(),
                    "MinDeltaBot": self.minDeltaBot.value(),
                    "MaxDeltaBot": self.maxDeltaBot.value(),
                    "DetailSettings": self.analyzer.get_current_settings()},
                    file, ensure_ascii=False)
        except Exception as e:
            print(e)
            pass

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        # Перед завершением сохраняем все настройки в файл
        self.save_breath_sett_to_json()
        self.closeWindowSignal.emit()

        # При закрытии приложения отключаемся от сервера
        self.network.disconnect()
        self.cam_obj.disconnect_camera()

        super().closeEvent(a0)

    def set_status_bar_text(self, text: str, style: str) -> None:
        self.statusbar.setText(text)
        self.statusbar.setStyleSheet(style)

    def set_logs_in_label(self) -> None:
        # Отображаем данные о зафиксированном вдохе
        num = len(self.signals_logs)
        data = self.signals_logs[num]
        self.breath_logs_label.appendPlainText(
            f"{num} | Time: {data['time']}\n "
            f"Upper delta: {data['upper']['delta']} \\ \n "
            f"Lower delta: {data['lower']['delta']}")

        # Если открыто окно, то загружаем и туда новое значение
        if self.breath_logs_win:
            self.breath_logs_win.set_data(num, data)

    def check_network_state(self, exp: str = None) -> None:
        # Проверка состояния соединения
        # Если есть ошибка, то выводим ее
        if exp is not None:
            self.set_status_bar_text(exp, 'background-color: rgb(170, 0, 0); '
                                          'color: rgb(255, 255, 255)')
            return
        if not self.network.is_open():
            self.set_status_bar_text('Нет соединения с сервером',
                                     'background-color: rgb(170, 0, 0); '
                                     'color: rgb(255, 255, 255)')
        else:
            self.set_status_bar_text('', 'background-color: transparent;')

    def catch_signal(self, data):
        # Добавляем в логи
        self.signals_logs[len(self.signals_logs) + 1] = data

        # Отображаем логи
        self.set_logs_in_label()

        # Отправляем сигнал на сервер
        self.network.send_signal()
