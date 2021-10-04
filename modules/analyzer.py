import numpy as np
import pyqtgraph as pg


class Analyser:
    def __init__(self, parent):
        self.parent = parent
        self.graph = Graph(self)

        self.colors = {}

    def add_next_position(self, name, position):
        self.colors[name] = position


class Graph:
    def __init__(self, parent):
        self.analyzer = parent

        self.chunkSize = 100
        # Remove chunks after we have 10
        self.maxChunks = 10
        self.startTime = pg.ptime.time()

        self.pl = parent.parent.graphicsView.addPlot(colspan=2)
        self.pl.setLabel('bottom', 'Time', 's')
        self.pl.setXRange(0, 10)
        self.curves = []
        self.data = np.empty((self.chunkSize + 1, 2))
        self.ptr = 0

        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    def update(self):
        now = pg.ptime.time()

        i = self.ptr % self.chunkSize
        if i == 0:
            curve = self.pl.plot(pen=(255,0,0), name='Red curve')
            self.curves.append(curve)
            last = self.data[-1]
            self.data = np.empty((self.chunkSize + 1, 2))
            self.data[0] = last
            while len(self.curves) > self.maxChunks:
                c = self.curves.pop(0)
                self.pl.removeItem(c)
        else:
            curve = self.curves[-1]
        self.data[i + 1, 0] = now - self.startTime
        # self.data[i + 1, 1] = np.random.normal()
        self.data[i + 1, 1] = self.analyzer.colors['Красный'][1] if 'Красный' in self.analyzer.colors else 0
        curve.setData(x=self.data[:i + 2, 0], y=self.data[:i + 2, 1])
        self.ptr += 1
