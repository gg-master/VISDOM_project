import time

import cv2
import numpy as np
from sys import platform
import threading
from data.settings.settings import *

from PyQt5.QtGui import QImage
from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel


class Camera:
    def __init__(self, name='Threading-Camera'):
        self.name = name
        self.cap = self.last_frame = self.ret = None
        self.is_restarted = False

        self._thread = None

        self.connect_to_device()
        self._open_thread()

    def _open_thread(self):
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self.run, name=self.name)
            self._thread.start()

    def _close_thread(self):
        self._thread.do_run = False
        self._thread.join()

    def _restart_thread(self):
        self._close_thread()
        self._open_thread()

    def disconnect_camera(self):
        self.release()
        self._close_thread()

    def connect_to_device(self):
        if platform == 'win32':
            self.cap = cv2.VideoCapture(0 + cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(-1)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        self.cap.set(cv2.CAP_PROP_FPS, 25)

    def read(self):
        return self.ret, self.last_frame

    def isOpened(self):
        return self.cap.isOpened() or self.is_restarted

    def release(self):
        if self.cap is not None:
            self.cap.release()

    def restart(self):
        if not self.is_restarted:
            self.is_restarted = True
            self.release()
            self.connect_to_device()
            # self._restart_thread()
            self.is_restarted = False

    def run(self):
        t = threading.currentThread()
        while getattr(t, "do_run", True) and \
                (self.cap.isOpened() or not self.is_restarted):
            if self.is_restarted:
                time.sleep(1.0)
                continue
            self.ret, self.last_frame = self.cap.read()


class WindowCamera(QThread):
    changePixmap = pyqtSignal(QImage)

    def __init__(self,  parent, label: QLabel, camera: Camera):
        super().__init__(parent)

        # Лэйбл, на котором будет отображаться картинка
        self.label = label

        self.is_run = True

        # Подключаем камеру
        self.cam = camera

    def release(self) -> None:
        self.cam.release()

    def stop(self):
        self.is_run = False

    def start(self, *args):
        self.is_run = True
        super().start()

    def restart(self):
        self.stop()
        self.start()


class MainWindowCamera(WindowCamera):
    def __init__(self, parent, label: QLabel, camera):
        super().__init__(parent, label, camera)

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
        while self.cam.isOpened() and self.label and self.is_run:
            # Считывание изображения
            ret, img = self.cam.read()

            if not ret and not self.cam.isOpened():
                break
            elif not ret and self.cam.isOpened():
                continue

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

                cv2.circle(img, (x, y), circle_radius, yellow_color, 2)
                cv2.putText(img, f"{x}-{y}", (x + 10, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, text_scale,
                            yellow_color, 2)
        return img


class ColorRangeCamera(WindowCamera):
    def __init__(self, parent, label: QLabel):
        super().__init__(parent, label, parent.camera.cam)
        # Устанавливаем начальные диапазоны
        self.hsv_min = np.array((0, 0, 0), np.uint8)
        self.hsv_max = np.array((255, 255, 255), np.uint8)

    def set_hmin_hmax(self, hsv_min: list, hsv_max: list) -> None:
        self.hsv_min = np.array(hsv_min, np.uint8)
        self.hsv_max = np.array(hsv_max, np.uint8)

    def run(self) -> None:
        # Пока камера работает получаем изображение и отображаем его
        while self.cam.isOpened() and self.label and self.is_run:
            # Считывание изображения
            ret, img = self.cam.read()

            if not ret:
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
