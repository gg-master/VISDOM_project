import colorsys
import numpy as np
import pyqtgraph as pg

from PyQt5.QtCore import pyqtSignal, QObject

from typing import List, Dict, Tuple, Any


class Graph:
    def __init__(self, analyzer, graphics_view, orig=True) -> None:
        # np.seterr(all='ignore')

        # Объект анализатора, из которого получаем координаты
        self.analyzer: Analyzer = analyzer

        # Флаг оригинальстости графика
        self.orig: bool = orig

        self.startTime = pg.ptime.time()

        # Объект, на котором будет рисоваться график
        self.pl = graphics_view.addPlot()

        self.pl.setLabel('bottom', 'Time', 's')

        # Словарь с пронумерованными кривыми
        self.curves: Dict[int: Dict[str: Any]] = {}

        # Кривые, которые уже отображались на графике
        self.saved_curves: Dict[int: Dict[str: Any]] = {}

        # Максимально количество данных для сохранения
        self.maxChunks: int = 300
        self.save_full_data: bool = False

        # Массив данных, заполненный нулями для двух кривых.
        self.data: np.ndarray = np.zeros((self.maxChunks, 5))

        # Счетчик для данных. Изменяется во времени
        self.ptr: int = 0

        # Таймер, который будет срабатывать каждые 50 миллисекунд,
        # и обновлять данные в графике
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

        # Если создается график в окне, и нам необходимо в нем отображать
        # данные главного графика, копируем значения из главного графика
        if not orig:
            self.startTime = self.analyzer.main_graph.startTime
            self.maxChunks = self.analyzer.main_graph.maxChunks
            self.save_full_data = self.analyzer.main_graph.save_full_data
            self.timer.setInterval(self.analyzer.main_graph.timer.interval())
            self.reload_curves()

    def reload_curves(self) -> None:
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

    def check_saved_curves(self) -> None:
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

    def update(self) -> None:
        now = pg.ptime.time()

        # Увеличиваем счетчик
        self.ptr += 1

        # Увеличиваем размерность массива данных при переполнении
        if self.ptr >= self.data.shape[0]:
            # Также очищаем массив c обнаруженными пиками
            self.analyzer.detected_peaks = self.analyzer.detected_peaks[
                                           -self.analyzer.leave_det_peaks:]

            tmp = self.data

            # Если не сохраняем весь массив
            if not self.save_full_data:
                # Обвноялвяем массив
                self.data = np.zeros((self.maxChunks, 5))

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

        if not self.orig and self.analyzer.colors:
            orig = self.analyzer.graphs[0]
            self.data = orig.data
            self.ptr = orig.ptr

        # Перебираем цвета, и отображаем их координаты на графике
        for num, val in self.analyzer.colors.items():
            if num not in self.curves:
                continue
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

    def get_rgb_by_name(self, name: str) -> list:
        """
        Переводим цвет по названию в rbg формат
        :param name - Имя цвета
        :return: rbg-list - Преобразованный hsv в rgb
        """
        hsv_min_max = self.analyzer.parent.colors[name]
        v1, v2 = hsv_min_max
        return list(map(lambda x: x * 100, colorsys.hsv_to_rgb(
            (v1[0] + v2[0]) / 200, 1, 1)))

    @staticmethod
    def get_key_by_name(name: str, dictionary: dict) -> int:
        for k, v in dictionary.items():
            if v['name'] == name:
                return k
        return -1

    def is_active(self) -> bool:
        """ Имеются ли на графике какие-либо кривые"""
        return bool(self.curves)

    def set_new_settings(self, **settings: [str, Any]) -> None:
        """ Обновляем настройки графика"""
        for k, v in settings.items():
            if k == 'timer_interval':
                self.timer.setInterval(settings[k])
            else:
                try:
                    getattr(self, k)
                    setattr(self, k, settings[k])
                except AttributeError:
                    continue


class Analyzer(QObject):
    newCoordinatesSignal = pyqtSignal()

    def __init__(self, main) -> None:
        super().__init__(main)
        self.parent = main

        self.colors: Dict[int, dict] = {}

        # Массив с данными, а также таймер срабатывания регистрации точек в
        # массиве находятся в главном графике, который создается здесь.
        self.main_graph: Graph = Graph(self, self.parent.graphicsView)
        self.graphs: List[Graph] = [self.main_graph]

        # Временной отрезок, который надо проанализировать (мс)
        tm_delta: int = 2000

        # Размер массива для анализа
        self.len_analyseData: int = self.set_len_analyse_data(tm_delta)

        # Список с метками времени, которые уже были обнаружены
        self.detected_peaks: List[float] = []
        self.leave_det_peaks: int = 10

        # Коэфф сглаживания
        self.window_len: int = 20

        self.delta_top: List[int, int] = [0, 0]
        self.delta_bot: List[int, int] = [0, 0]

    def analyse(self) -> None:
        """
        Предварительная фильтровка данных и получение экстремумов
        :return:
        """
        if not self.graphs[0].is_active() or \
                len(self.graphs[0].curves) < 2:
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
        y1_smooth: np.ndarray = self.smooth_line(y1_graph)
        y2_smooth: np.ndarray = self.smooth_line(y2_graph)

        # Находим пики для каждой сглаженной прямой
        y1_peaks: List = self.find_peaks(y1_smooth)
        y2_peaks: List = self.find_peaks(y2_smooth)

        self.analyse_peaks(y1_peaks, y2_peaks, data)

    def analyse_peaks(self, y1_p: List[List[int]], y2_p: List[List[int]],
                      data: np.ndarray) -> None:
        """
        Анализирование экстремумов
        :param y1_p - y1_peaks
        :param y2_p - y2_peaks
        :param data - dictionary with all data
        :return: None
        """
        y1_max_p, y1_min_p = y1_p[1], y1_p[2]
        y2_max_p, y2_min_p = y2_p[1], y2_p[2]

        # Если экстремумов недостаточно - выходим
        if len(y1_p[0]) < 3 and len(y2_p[0]) < 3:
            return

        # Если и максимумов и минимумов больше, чем необходимо,
        # получаем последний всплеск
        if len(y1_max_p) > 2 and len(y1_min_p) > 1:
            y1_max_p, y1_min_p = self.find_last_peak(y1_max_p, y1_min_p)
        if len(y2_max_p) > 2 and len(y2_min_p) > 1:
            y2_max_p, y2_min_p = self.find_last_peak(y2_max_p, y2_min_p)

        # Если обнаружено нужное количество максимумов и миниимумов,
        # то проверяем подходит ли всплеск под нормативы
        if (len(y1_max_p) == 2 and len(y1_min_p) == 1) and \
                (len(y2_max_p) == 2 and len(y2_min_p) == 1):

            # Координата времени в которую был зафиксирован пик всплеска
            p1_time, p2_time = data[y1_min_p[0]][0], data[y2_min_p[0]][0]

            # Преобразуем номера вершин в их координаты (y, x)
            y1_max_p = list(map(lambda x: (data[x][1], data[x][3]), y1_max_p))
            y1_min_p = (data[y1_min_p[0]][1], data[y1_min_p[0]][3])
            y2_max_p = list(map(lambda x: (data[x][2], data[x][4]), y2_max_p))
            y2_min_p = (data[y2_min_p[0]][1], data[y2_min_p[0]][3])

            # Получаем установленную дельту для верхей и нижней точек
            is_y1_top = True if y1_min_p[1] < y2_min_p[1] else False
            normal_delta1 = self.delta_top if is_y1_top else self.delta_bot
            normal_delta2 = self.delta_bot if is_y1_top else self.delta_top

            delta1 = sum(map(lambda x: x[0], y1_max_p)) // 2 - y1_min_p[0]
            delta2 = sum(map(lambda x: x[0], y2_max_p)) // 2 - y2_min_p[0]

            if normal_delta1[0] <= delta1 <= normal_delta1[1] and \
                    normal_delta2[0] <= delta2 <= normal_delta2[1] and \
                    p1_time not in self.detected_peaks and \
                    p2_time not in self.detected_peaks:

                self.process_signal(self.create_data(p1_time, [delta1, delta2],
                                                     is_y1_top,
                                                     [y1_max_p, y1_min_p,
                                                     y2_max_p, y2_min_p]))
                # Сохраняем время вершины всплеска, чтобы несколько раз
                # подряд не обрабатывать один и тот-же всплеск
                self.detected_peaks.extend([p1_time, p2_time])

    def smooth_line(self, array: np.ndarray) -> np.ndarray:
        """
        Сглаживание кривой
        :param: numpy.ndarray
        :return: numpy.ndarray
        """
        kernel = np.ones(self.window_len, dtype=float) / self.window_len
        return np.convolve(array, kernel, 'same')

    @staticmethod
    def find_last_peak(max_peaks: List[int], min_peaks: List[int]) -> tuple:
        """
        Возвращает последний всплеск из переданных значений
        :param max_peaks: Все верхние экстремумы
        :param min_peaks: Все нижние экстремумы
        :return: [[max_peak1, max_peak2], [min_peak]]
        """
        f = max(max_peaks)
        m = sorted(filter(lambda x: x < f, min_peaks))[-1]
        s = sorted(filter(lambda x: x < m, max_peaks))[-1]
        return [s, f], [m]

    @staticmethod
    def find_peaks(array: np.ndarray) -> List[List[int]]:
        # Находим экстремумы используя втроенную функцию
        row_peaks = np.diff(np.sign(np.diff(array)))

        peaks: List[int] = row_peaks.nonzero()[0] + 1
        peaks_min: List[int] = (row_peaks > 0).nonzero()[0] + 1
        peaks_max: List[int] = (row_peaks < 0).nonzero()[0] + 1
        return [peaks, peaks_max, peaks_min]

    @staticmethod
    def create_data(time: float, deltas: list, is_y1_top: bool,
                    peaks: list) -> dict:
        d1, d2 = deltas
        max_p1, min_p1, max_p2, min_p2 = peaks
        # Проебразуем данные о всплеске
        data = {
            'time': round(time, 2),
            'upper': {
                'delta': d1 if is_y1_top else d2,
                'max': list(map(lambda x: x[0],
                                max_p1 if is_y1_top else max_p2)),
                'min': min_p1[0] if is_y1_top else min_p2[0]
            }, 'lower': {
                'delta': d2 if is_y1_top else d1,
                'max': list(map(lambda x: x[0],
                                max_p2 if is_y1_top else max_p1)),
                'min': min_p2[0] if is_y1_top else min_p1[0]
            }
        }
        return data

    def set_len_analyse_data(self, tm_delta: int) -> int:
        # Устанавливаем размер среза данных в зависимости от времени
        return tm_delta // self.graphs[0].timer.interval()

    def set_new_settings(self, **settings: [str, Any]) -> None:
        # Обновляем настройки анализатора
        for k, v in settings.items():
            if k == 'timeDelta':
                self.len_analyseData = self.set_len_analyse_data(settings[k])
            else:
                try:
                    # Пробуем найти в собственном классе необходимый атрибут
                    getattr(self, k)
                    # Изменяем значение атрибута, если нашли
                    setattr(self, k, v)
                except AttributeError:
                    # Проверяем имеется ли атрибут в объектах графиков
                    [i.set_new_settings(**{k: v}) for i in self.graphs]
                    continue

    def add_next_position(self, name: str, position: Tuple[int, int]) -> None:
        # Полученный цвет загружаем в соответствующий блок
        self.colors[self.get_key_by_name(name)]['pos'] = position

    def update_colors(self, new_colors: Dict[int, Dict[str, str]]) -> None:
        # Обновляем набор цветов
        self.colors = new_colors

        # Перезагружаем кривые графиков
        [graph.reload_curves() for graph in self.graphs]

    def get_key_by_name(self, name: str) -> int:
        for k, v in self.colors.items():
            if v['name'] == name:
                return k
        return -1

    def get_last_coordinates(self) -> List[int]:
        return self.main_graph.data[self.main_graph.ptr][1:]

    def get_analyse_data(self) -> np.ndarray:
        # Возвращает срех данных для анализа
        return self.main_graph.data[
               self.main_graph.ptr - self.len_analyseData
               if self.main_graph.ptr > self.len_analyseData
               else 0: self.main_graph.ptr]

    def get_current_settings(self) -> Dict[str, Any]:
        # Собираем сохрняемые данные
        return {'window_len': self.window_len,
                'save_full_data': self.main_graph.save_full_data,
                'timer_interval': self.main_graph.timer.interval(),
                'maxChunks': self.main_graph.maxChunks}

    def add_graph(self, graph: Graph) -> None:
        self.graphs.append(graph)

    def remove_graph(self, graph: Graph) -> None:
        if graph in self.graphs:
            self.graphs.remove(graph)

    def process_signal(self, data: Dict[Any, Any]) -> None:
        # Обрабатываем сигнал
        print(f'Work || {data}')

        # Фиксируем сигнал
        self.parent.catch_signal(data)
