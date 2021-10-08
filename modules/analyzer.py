import colorsys
import numpy as np
import pyqtgraph as pg

from PyQt5.QtCore import pyqtSignal, QObject


class Analyser(QObject):
    newCoordinatesSignal = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.colors = {}

        # Массив с данными, а также таймер срабатывания регистрации точек в
        # массиве находятся в главном графике, который создается здесь.
        self.graphics = [Graph(self, self.parent.graphicsView)]

    def add_next_position(self, name, position):
        # Полученный цвет загружаем в соответствующий блок
        self.colors[self.get_key_by_name(name)]['pos'] = position

    def update_colors(self, new_colors: dict):
        # Обновляем набор цветов
        self.colors = new_colors
        # Перезагружаем кривые графиков
        [graph.reload_curves() for graph in self.graphics]

    def get_key_by_name(self, name) -> int:
        for k, v in self.colors.items():
            if v['name'] == name:
                return k
        return -1

    def add_graph(self, graph):
        self.graphics.append(graph)

    def remove_graph(self, graph):
        self.graphics.remove(graph)

    def get_last_coordinates(self):
        main_graph = self.graphics[0]
        return main_graph.data[main_graph.ptr][1:]


class Graph:
    def __init__(self, analyzer, graphics_view, orig=True):
        # np.seterr(all='ignore')
        # Объект анализатора, из которого получаем координаты
        self.analyzer = analyzer

        # Флаг оригинальстости графика
        self.orig = orig

        self.startTime = pg.ptime.time()

        # Объект, на котором будет рисоваться график
        self.pl = graphics_view.addPlot()

        self.pl.setLabel('bottom', 'Time', 's')

        # Словарь с пронумерованными кривыми
        self.curves = {}

        # Кривые, который уже отображались на графике
        self.saved_curves = {}

        # Максимально количество данных для сохранения
        self.maxChunks = 300
        self.save_full_data = False

        # Массив данных, заполненный нулями для двух кривых.
        self.data = np.zeros((self.maxChunks, 5))

        # Счетчик для данных. Изменяется во времени
        self.ptr = 0

        # Таймер, который будет срабатывать каждые 50 миллисекунд,
        # и обновлять данные в графике
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

        # Если создается график в окне, и нам необходимо в нем отображать
        # данные главного графика, копируем значения из главного графика
        if not orig:
            orig = self.analyzer.graphics[0]
            self.startTime = orig.startTime

    def reload_curves(self):
        # Сохраняем объекты кривых, для последующего редактирования
        self.saved_curves.update(self.curves.copy())

        # Очищаем словарь с кривыми
        self.curves.clear()

        # Заполняем словарь новыми данными
        self.curves = {num: {'name': val['name'], 'curve': self.pl.plot(
            pen=self.get_rgb_by_name(val['name']))}
                       for num, val in self.analyzer.colors.items()
                       if val['name'] is not None}

        self.check_saved_curves()

    def check_saved_curves(self):
        if len(self.saved_curves) <= 1:
            return

        # Если новый цвет кривой того же номера не совпадает со старым,
        # то перекрашиваем кривую, у которой совпал цвет
        for k, v in self.curves.items():
            if v['name'] != self.saved_curves[k]['name']:
                num = self.get_key_by_name(v['name'], self.saved_curves)
                if num > 0:
                    curve = self.saved_curves[num]['curve']

                    # Устанавливаем кривой белый цвет и отрисовываем
                    curve.setPen((255, 255, 255))
                    curve.setData(x=self.data[:self.ptr, 0],
                                  y=self.data[:self.ptr, num])

    def update(self):
        now = pg.ptime.time()

        # Увеличиваем счетчик
        self.ptr += 1

        # Увеличиваем размерность массива данных при переполнении
        if self.ptr >= self.data.shape[0]:
            tmp = self.data

            # Если не сохраняем весь массив
            if not self.save_full_data:
                # Обвноялвяем массив
                self.data = np.zeros((self.data.shape[0], 5))

                # Перемащаем в него копию последних 1/4 значений
                self.data[:tmp.shape[0] // 4] = tmp[-tmp.shape[0] // 4:]

                # Перемещаем счетчик
                self.ptr = tmp.shape[0] // 4

                # Очищаем график от старых значений
                if self.curves:
                    self.pl.clear()
                    self.curves.clear()
                    self.saved_curves.clear()
                    self.reload_curves()

            else:
                # Увеличиваем массив вдвое
                self.data = np.zeros((self.data.shape[0] * 2, 5))
                self.data[:tmp.shape[0]] = tmp

        # Указываем координату времени
        self.data[self.ptr, 0] = now - self.startTime

        # Перебираем цвета, и отображаем их координаты на графике
        for num, val in self.analyzer.colors.items():
            if num not in self.curves:
                continue

            if not self.orig:
                orig = self.analyzer.graphics[0]
                self.data = orig.data
                self.ptr = orig.ptr

            else:
                # Устанавливаем координату Y цвета
                y = val['pos'][0] if 'pos' in val else 0
                x = val['pos'][1] if 'pos' in val else 0
                self.data[self.ptr, num] = y
                self.data[self.ptr, num + 2] = x
            # Отрисовываем на графике
            self.curves[num]['curve'].setData(x=self.data[:self.ptr, 0],
                                              y=self.data[:self.ptr, num])

        # Сигналем в анализаторе о том, что появились новые координаты
        self.analyzer.newCoordinatesSignal.emit()

    def get_rgb_by_name(self, name):
        """
        Переводим цвет по названию в rbg формат
        :param name: Имя цвета
        :return: rbg-tuple
        """
        hsv_min_max = self.analyzer.parent.colors[name]
        v1, v2 = hsv_min_max
        return list(map(lambda x: x * 100, colorsys.hsv_to_rgb(
            (v1[0] + v2[0]) / 200, 1, 1)))

    @staticmethod
    def get_key_by_name(name, dictionary) -> int:
        for k, v in dictionary.items():
            if v['name'] == name:
                return k
        return -1
