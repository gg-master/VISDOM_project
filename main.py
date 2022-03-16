import sys

from PyQt5.QtWidgets import QApplication

from modules.camera_views import Camera
from modules.main_window import MainWindow
from modules.network import Network


def exception_hook(exc_type, value, traceback):
    print(exc_type, value, traceback)
    sys._excepthook(exc_type, value, traceback)
    sys.exit(1)


class Main:
    def __init__(self) -> None:
        self.network = Network()
        self.camera = Camera()

        # Создаем приложение и запускаем главное окно
        app = QApplication(sys.argv)

        self.main_window = MainWindow(self.camera, self.network)
        self.main_window.show()

        # Подключаем сигнал с ошибками к главному окно для их отображения
        self.network.exceptionSignal.connect(
            self.main_window.check_network_state)

        sys.exit(app.exec())


if __name__ == '__main__':
    sys.excepthook = exception_hook
    Main()
