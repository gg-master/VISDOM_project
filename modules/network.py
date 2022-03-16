import asyncio
import json
import random
import socket
import string
from _thread import start_new_thread

import websockets
from PyQt5.QtCore import QObject, pyqtSignal


class Network(QObject):
    exceptionSignal = pyqtSignal(str)

    pi_data = {
        'status': 'registration',
        'type': 'pi',
        'token': -1
    }

    def __init__(self):
        super().__init__(parent=None)
        # url = 'ws://127.0.0.1:8765'
        # self.addr = "ws://localhost:8080"
        self.addr = self.token = None

        self.alive = False
        self.send_data = self.received_data = None

        # Ответ после подключения
        self.conn_resp = None
        # Индетификационный код последнего сообщения
        self.last_vcode = ''

    def open_connection(self, address, token):
        # Open new connection with server
        self.addr, self.token = address, token

        start_new_thread(self.start_async, ())

    def send_signal(self) -> None:
        # Если открыто соединение с сервером, то отправляем сигнал
        if self.is_open():
            self.net.set_send_get_recv({'signal': True})

    def set_send_get_recv(self, data):
        # Генерируем уникальный код, который будет отвечает за определенную
        # версию
        # ВВЕДЕНО Чтобы отслеживать изменения данных, которые необходимо
        # отправить на сервер
        self.send_data = self.generate_version_code(data)
        return self.received_data

    @staticmethod
    def generate_version_code(data):
        # Генерация кода, для отличия сообщений между собой
        symbols = list(string.ascii_uppercase + string.digits)
        data.update({'vcode': ''.join(random.sample(symbols, 6))})
        return data

    def validate_reg_data(self):
        # Проверка на валидность токена
        if self.token:
            self.pi_data['token'] = int(self.token)
            return True
        return False

    def start_async(self):
        asyncio.run(self.start_client())

    async def start_client(self):
        try:
            async with websockets.connect(self.addr) as websocket:
                self.alive = True

                # Проверяем данные, которые отправляются для регистрации
                if not self.validate_reg_data():
                    raise Exception('Токен не прошел валидацию')
                await websocket.send(json.dumps(self.pi_data))

                # Ответ об успешном подключении
                self.conn_resp = json.loads(await websocket.recv())
                print(self.conn_resp)

                # Если не удалось подключиться к серверу, выдаем ошибку
                if self.conn_resp['answer'] != 'Successful registration of ' \
                                               'your client':
                    raise Exception(self.conn_resp['answer'])

                # Начинаем общаться с сервером
                while True:
                    # Если соединение закрыто, отправляем сигнал на сервер
                    if not self.alive:
                        await websocket.send(
                            json.dumps({'status': 'Close connection'}))
                        break
                    try:
                        # Устанавливаем тайм-аут для функции считывания данных
                        # из буфера.
                        self.received_data = json.loads(
                            await asyncio.wait_for(
                                websocket.recv(), timeout=1.0))
                    except asyncio.TimeoutError:
                        # Благодаря тайм-ауту отключаем блокировку цикла на
                        # время получения данных.
                        continue
                    print(self.received_data)

                    if self.received_data['answer'] == 'Start sharing':
                        # Главный цикл, который отправляет данные на сервер
                        while self.alive:
                            # Если данные обновились,
                            # то отправляем их на сервер
                            if self.send_data is not None and \
                                    self.last_vcode != self.send_data['vcode']:
                                self.last_vcode = self.send_data['vcode']

                                await websocket.send(json.dumps(
                                    {'status': 'sharing',
                                     'data': self.send_data}))

                            # Играем в пинг-понг, чтобы поддерживать
                            # соединение с сервером
                            pong_waiter = await websocket.ping()
                            await pong_waiter
                            pong_waiter.result()
                        print('close conn')
                        # Закрываем соединение с сервером
                        await websocket.send(
                            json.dumps({'status': 'Close connection'}))
                        break

                    elif self.received_data['answer'] == \
                            'Pair has been established':
                        await websocket.send(json.dumps(
                            {'status': 'I am ready to get'}))

                    elif self.received_data['answer'] == 'sharing':
                        print('received_data', self.received_data['data'])
                    else:
                        # Если пришли какие-то другие команлы, то выдаем ошибку
                        raise Exception(self.received_data['answer'])
        except Exception as e:
            self.exceptionSignal.emit(self.validate_exception(e))
            print('exc in network:', e)
        finally:
            self.alive = False

    def disconnect(self):
        self.alive = False
        self.addr = self.token = None
        self.send_data = self.received_data = self.conn_resp = None
        self.last_vcode = ''

    def is_open(self):
        return self.alive

    @staticmethod
    def validate_exception(exc):
        try:
            raise exc
        except (ConnectionRefusedError, socket.gaierror):
            return 'Проверьте состояние интернета и попробуйте снова.'
        except Exception as e:
            return str(e) if str(e) else 'Соединение с сервером разорвано.'


if __name__ == '__main__':
    net = Network()
    net.open_connection('ws://localhost:8080', 1234)
