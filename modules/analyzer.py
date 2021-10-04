import numpy as np
import pyqtgraph as pg
import colorsys


class Analyser:
    def __init__(self, parent):
        self.parent = parent

        self.colors = dict()

        self.graph = Graph(self)

    def add_next_position(self, name, position):
        # Если цвета раньше не было в наборе, то создаем новую кривую для него
        if name not in self.colors:
            self.colors[name] = position
            self.graph.reload_curves()
        else:
            # Иначе просто обновляем координаты
            self.colors[name] = position

    def update_colors(self, new_colors: dict):
        # Все цвета, которые не вошли в новый набор цветов удаляются
        print(self.colors, end=' ')
        self.colors = {name: self.colors[name]
                       for name in filter(
                lambda x: x in new_colors, self.colors.keys())}
        # Перезагружаем кривые графика, что остановить отрисовку,
        # если нет нужного цвета
        self.graph.reload_curves()
        print(self.colors, new_colors)


class Graph:
    def __init__(self, parent):
        # np.seterr(all='ignore')
        self.analyzer = parent

        self.startTime = pg.ptime.time()

        self.pl = parent.parent.graphicsView.addPlot()
        self.pl.setLabel('bottom', 'Time', 's')
        self.pl.setXRange(0, 20)

        self.curves = []
        self.reload_curves()

        self.data = np.empty((100, 3))

        self.ptr = 0

        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    def reload_curves(self):
        print(self.analyzer.colors)
        for num, name in enumerate(self.analyzer.colors.keys()
                                   if len(self.curves) >= 2 else range(2),
                                   start=1):
            if len(self.curves) < num:
                self.curves.append(
                    self.pl.plot(pen=(255, 255, 255)))
            else:
                self.curves[num].setPen(
                    self.get_rgb_by_name(self.analyzer.colors[name]))
        print(self.curves)

    def update(self):
        now = pg.ptime.time()
        self.ptr += 1
        # print(self.data.shape[0], self.ptr)

        # Увеличиваем размерность массива данных
        if self.ptr >= self.data.shape[0]:
            tmp = self.data
            self.data = np.empty((self.data.shape[0] * 2, 3))
            self.data[:tmp.shape[0]] = tmp

        self.data[self.ptr, 0] = now - self.startTime
        # self.data[i + 1, 1] = np.random.normal()
        for num, val in enumerate(self.curves, start=1):
            y = list(self.analyzer.colors.values())[num - 1][0] \
                if num <= len(self.analyzer.colors) else 0
            # print(f'{num} -- {y}')
            self.data[self.ptr, num] = y
            self.curves[num - 1].setData(x=self.data[:self.ptr, 0],
                                         y=self.data[:self.ptr, num])

    def get_rgb_by_name(self, name):
        hsv_min_max = self.analyzer.parent.colors[name]
        v1, v2 = hsv_min_max
        return list(map(lambda x: x * 100, colorsys.hsv_to_rgb(
            (v1[0] + v2[0]) / 200, 1, 1)))
