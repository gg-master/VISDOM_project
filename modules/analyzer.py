import numpy as np
import pyqtgraph as pg
import colorsys


class Analyser:
    def __init__(self, parent):
        self.parent = parent

        self.curr_colors = {}
        self.colors_pos = {}

        self.graph = Graph(self)

    def add_next_position(self, name, position):
        self.colors_pos[name] = position

    def update_colors(self, new_colors: dict):
        # Все цвета, которые не вошли в новый набор цветов удаляются
        print(self.curr_colors, end=' ')
        self.curr_colors = new_colors
        print(self.curr_colors, new_colors)

        self.graph.create_curves()


class Graph:
    def __init__(self, parent):
        # np.seterr(all='ignore')
        self.analyzer = parent

        self.startTime = pg.ptime.time()

        self.pl = parent.parent.graphicsView.addPlot()
        self.pl.setLabel('bottom', 'Time', 's')

        self.curves = {}

        self.data = np.empty((100, 3))

        self.ptr = 0

        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    def create_curves(self):
        for num, val in self.analyzer.curr_colors.items():
            if val:
                self.curves[num] = self.pl.plot(
                    pen=self.get_rgb_by_name(list(val.keys())[0]))

    def update(self):

        now = pg.ptime.time()
        self.ptr += 1
        # print(self.data.shape[0], self.ptr)
        if self.ptr >= self.data.shape[0]:
            tmp = self.data
            self.data = np.empty((self.data.shape[0] * 2, 3))
            self.data[:tmp.shape[0]] = tmp

        self.data[self.ptr, 0] = now - self.startTime
        # self.data[i + 1, 1] = np.random.normal()
        for n, val in self.analyzer.curr_colors.items():
            if val:
                name = list(val.keys())[0]

                y = self.analyzer.colors_pos[name][0] \
                    if name in self.analyzer.colors_pos else 0
                # print(name, y)
                self.data[self.ptr, n + 1] = y
                self.curves[n].setData(x=self.data[:self.ptr, 0],
                                       y=self.data[:self.ptr, n + 1])

    def get_rgb_by_name(self, name):
        hsv_min_max = self.analyzer.parent.colors[name]
        v1, v2 = hsv_min_max
        return list(map(lambda x: x * 100, colorsys.hsv_to_rgb(
            (v1[0] + v2[0]) / 200, 1, 1)))
