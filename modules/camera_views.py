import cv2
import numpy as np
from sys import platform

from PyQt5.QtGui import QImage
from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel

YELLOW = (0, 255, 255)


class Camera:
    def __init__(self):
        if platform == 'win32':
            self.cap = cv2.VideoCapture(0 + cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(-1)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)

    def get_capture(self) -> cv2.VideoCapture:
        return self.cap


class MainWindowCamera(QThread):
    changePixmap = pyqtSignal(QImage)

    def __init__(self, parent, label: QLabel):
        super().__init__(parent)

        # Лэйбл, на котором будет отображаться картинка
        self.label = label

        # Подключаем камеру
        self.cap: cv2.VideoCapture = Camera().get_capture()

        # Список цветов для распознавния
        self.current_colors = {}

    def set_current_colors(self, colors_array: dict) -> None:
        # Формируем новый список цветов для распознавания
        new_colors = {k: [np.array(v[0], np.uint8),
                          np.array(v[1], np.uint8)]
                      for k, v in colors_array.items()}
        self.current_colors = new_colors

    def run(self) -> None:
        # Пока камера работает получаем изображение и отображаем его
        while self.cap.isOpened() and self.label:
            # Считывание изображения
            flag, img = self.cap.read()

            if not flag:
                break

            # Получаем картикну с отмеченными распознанными объектами
            img = self.get_img_with_objects(img)

            # Переводим в формат для qt
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_img.shape
            bytes_per_line = ch * w
            convert_to_qt_format = QImage(rgb_img.data, w, h, bytes_per_line,
                                          QImage.Format_RGB888)
            try:
                # Мастшабируем в соответствии с размерами экрана
                p = convert_to_qt_format.scaled(
                    self.label.width(), self.label.height(),
                    Qt.KeepAspectRatio)
                # Вызываем событие об обновлении картинки
                self.changePixmap.emit(p)
            except Exception:
                pass

    def get_img_with_objects(self, img: np.ndarray) -> np.ndarray:
        img = cv2.flip(img, 1)  # отражение кадра вдоль оси Y
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        for name, color in self.current_colors.items():
            hsv_min, hsv_max = color

            # Распознавание цвета куба
            thresh = cv2.inRange(hsv, hsv_min, hsv_max)

            moments = cv2.moments(thresh, 1)
            dM01 = moments['m01']
            dM10 = moments['m10']
            dArea = moments['m00']

            # Отрисовка координат куба
            if dArea > 100:
                x = int(dM10 / dArea)
                y = int(dM01 / dArea)

                try:
                    # Добавляем новые координаты для точки определенного цвета
                    self.parent().analyzer.add_next_position(name, (x, y))
                except Exception as e:
                    # print('camera_views.py:100 // exp //', e)
                    pass

                cv2.circle(img, (x, y), 5, YELLOW, 2)
                cv2.putText(img, f"{x}-{y}", (x + 10, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, YELLOW, 2)
        return img

    def release(self) -> None:
        self.cap.release()


class ColorRangeCamera(QThread):
    changePixmap = pyqtSignal(QImage)

    def __init__(self, parent, label: QLabel):
        super().__init__(parent)

        # Лэйбл, на котором будет отображаться картинка
        self.label = label

        # Подключаем камеру
        # self.cap = cv2.VideoCapture(cv2.CAP_ANY)
        self.cap: cv2.VideoCapture = parent.camera.cap

        # Устанавливаем начальные диапазоны
        self.hsv_min = np.array((0, 0, 0), np.uint8)
        self.hsv_max = np.array((255, 255, 255), np.uint8)

    def set_hmin_hmax(self, hsv_min: list, hsv_max: list) -> None:
        self.hsv_min = np.array(hsv_min, np.uint8)
        self.hsv_max = np.array(hsv_max, np.uint8)

    def run(self) -> None:
        # Пока камера работает получаем изображение и отображаем его
        while self.cap.isOpened() and self.label:
            # Считывание изображения
            status, img = self.cap.read()

            if not status:
                break

            # Преобразование в hsv картинку
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            # Выделение нужных цветов на картинке по установленным диапазонам
            thresh = cv2.inRange(hsv, self.hsv_min, self.hsv_max)

            # Переводим в формат для qt
            rgb_img = cv2.cvtColor(thresh, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_img.shape
            bytes_per_line = ch * w
            convert_to_qt_format = QImage(rgb_img.data, w, h, bytes_per_line,
                                          QImage.Format_RGB888)
            try:
                # Мастшабируем в соответствии с размерами экрана
                p = convert_to_qt_format.scaled(
                    self.label.width(), self.label.height(),
                    Qt.KeepAspectRatio)
                # Вызываем событие об обновлении картинки
                self.changePixmap.emit(p)
            except Exception:
                pass
