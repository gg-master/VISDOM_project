from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtGui import QImage
import cv2
import numpy as np

# Желтый цвет настроить
y_hsv_min = np.array((19, 194, 104), np.uint8)
y_hsv_max = np.array((38, 255, 208), np.uint8)

# Красный цвет
r_hsv_min = np.array((0, 109, 82), np.uint8)
r_hsv_max = np.array((7, 212, 178), np.uint8)

color_yellow = (0, 255, 255)


class MainWindowCamera(QThread):
    changePixmap = pyqtSignal(QImage)

    def __init__(self, parent, label, *args, **kwargs):
        super().__init__(parent)
        self.label = label
        self.cap = cv2.VideoCapture(0 + cv2.CAP_DSHOW)

    def run(self):
        while self.cap.isOpened() and self.label:
            flag, img = self.cap.read()

            if not flag:
                break
            img = self.get_img_with_objects(img)
            rgbImage = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgbImage.shape
            bytesPerLine = ch * w
            convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine,
                                       QImage.Format_RGB888)
            # p = convertToQtFormat
            p = convertToQtFormat.scaled(
                self.label.width(), self.label.height(), Qt.KeepAspectRatio)
            self.changePixmap.emit(p)

    def get_img_with_objects(self, img):
        # TODO дописать записывание и передачу координат в основное окно
        img = cv2.flip(img, 1)  # отражение кадра вдоль оси Y
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # Распознавание желтого куба
        y_thresh = cv2.inRange(hsv, y_hsv_min, y_hsv_max)

        y_moments = cv2.moments(y_thresh, 1)
        dM01 = y_moments['m01']
        dM10 = y_moments['m10']
        dArea = y_moments['m00']
        # Отрисовка желтого куба
        if dArea > 100:
            x = int(dM10 / dArea)
            y = int(dM01 / dArea)
            cv2.circle(img, (x, y), 5, color_yellow, 2)
            cv2.putText(img, "%d-%d" % (x, y), (x + 10, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color_yellow, 2)

        # Распознование красного куба
        r_thresh = cv2.inRange(hsv, r_hsv_min, r_hsv_max)
        r_moments = cv2.moments(r_thresh, 1)

        dM01 = r_moments['m01']
        dM10 = r_moments['m10']
        dArea = r_moments['m00']
        # Отрисовка красного куба
        if dArea > 100:
            x = int(dM10 / dArea)
            y = int(dM01 / dArea)
            cv2.circle(img, (x, y), 5, color_yellow, 2)
            cv2.putText(img, "%d-%d" % (x, y), (x + 10, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color_yellow, 2)
        return img


class ColorRangeCamera(QThread):
    def __init__(self, parent, label, *args, **kwargs):
        super().__init__(parent)
        self.label = label
        self.cap = cv2.VideoCapture(0 + cv2.CAP_DSHOW)

    changePixmap = pyqtSignal(QImage)

    def run(self):
        while self.cap.isOpened() and self.label:
            flag, img = self.cap.read()
            if not flag:
                break
            # img = self.get_img_with_objects(img)
            rgbImage = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgbImage.shape
            bytesPerLine = ch * w
            convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine,
                                       QImage.Format_RGB888)
            p = convertToQtFormat.scaled(
                self.label.width(), self.label.height(), Qt.KeepAspectRatio)
            self.changePixmap.emit(p)
