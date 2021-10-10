import colorsys
import numpy as np
import pyqtgraph as pg

from PyQt5.QtCore import pyqtSignal, QObject


class Analyzer(QObject):
    newCoordinatesSignal = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.colors = {}

        # Массив с данными, а также таймер срабатывания регистрации точек в
        # массиве находятся в главном графике, который создается здесь.
        self.graphics = [Graph(self, self.parent.graphicsView)]

        # Временной отрезок, который надо проанализировать (мс)
        tm_delta = 2000

        self.set_len_analyseData = \
            lambda x: x // self.graphics[0].timer.interval()
        # Размер массива для анализа
        self.len_analyseData = self.set_len_analyseData(tm_delta)

        # Список с метками времени, которые уже были обнаружены
        self.detected_localMinMax = []

        # Коэфф сглаживания
        self.window_len = 20

        # Направление, в какую сторону человек дышит. Влево - 1, Вправо - -1
        self.direction = 1

        self.delta_top = [0, 0]
        self.delta_bot = [0, 0]

    def analyse(self):
        if not self.graphics[0].is_active() or \
                len(self.graphics[0].curves) < 2:
            return

        data = self.get_analyse_data()

        # Если все значения по X и Y одного элемента равны 0, то не анализируем
        if all(map(lambda x: x[1] == 0 and x[3] == 0, data)) or \
                all(map(lambda x: x[2] == 0 and x[4] == 0, data)):
            return

        # Если точки меняют положение по X между собой, то не анализируем
        if (not all(map(lambda x: x[3] > x[4], data))) and \
                (not all(map(lambda x: x[4] > x[3], data))):
            return

        # Вытаскиваем из данных только значения по Y для каждой прямой
        y1_graph = np.array([int(data[i][1]) for i in range(data.shape[0])])
        y2_graph = np.array([int(data[i][2]) for i in range(data.shape[0])])

        # Сглаживаем прямые
        y1_smooth = self.smooth_line(y1_graph)
        y2_smooth = self.smooth_line(y2_graph)

        # Находим пики для каждой прямой
        y1_peaks = self.find_peaks(y1_smooth)
        y2_peaks = self.find_peaks(y2_smooth)
        print(f'{data[0][0]} - {data[-1][0]} // {y1_peaks[0]} '
              f'({str(y1_peaks[1]), str(y1_peaks[2])}), {y2_peaks[0]} '
              f'({str(y2_peaks[1]), str(y2_peaks[2])})')

    def smooth_line(self, array):
        kernel = np.ones(self.window_len, dtype=float) / self.window_len
        return np.convolve(array, kernel, 'same')

    @staticmethod
    def find_peaks(array) -> list:
        row_peaks = np.diff(np.sign(np.diff(array)))
        peaks = row_peaks.nonzero()[0] + 1
        peaks_min = (row_peaks > 0).nonzero()[0] + 1
        peaks_max = (row_peaks < 0).nonzero()[0] + 1
        return [peaks, peaks_max, peaks_min]

    def set_new_settings(self, dct):
        # Обновляем значения для анализа
        self.len_analyseData = self.set_len_analyseData(dct['timeDelta'])
        self.direction = dct['direction']
        self.delta_top = dct['delta_top']
        self.delta_bot = dct['delta_bot']

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

    def get_last_coordinates(self):
        main_graph = self.graphics[0]
        return main_graph.data[main_graph.ptr][1:]

    def get_analyse_data(self):
        graph = self.graphics[0]
        return graph.data[graph.ptr - self.len_analyseData
                          if graph.ptr > self.len_analyseData else 0:graph.ptr]

    def add_graph(self, graph):
        self.graphics.append(graph)

    def remove_graph(self, graph):
        self.graphics.remove(graph)


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

        # Кривые, которые уже отображались на графике
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

        self.analyzer.analyse()

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

    def is_active(self):
        return bool(self.curves)
