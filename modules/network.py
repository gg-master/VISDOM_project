import json
import random
import string
import asyncio
import websockets
from _thread import *

from PyQt5.QtCore import QObject, pyqtSignal


class Network(QObject):
    exceptionSignal = pyqtSignal(str)

    pi_data = {
        'status': 'registration',
        'type': 'pi',
        'token': None
    }

    def __init__(self, parent, addr, token, is_test=False):
        super().__init__(parent)
        # url = 'ws://127.0.0.1:8765'
        # self.addr = "ws://localhost:8080"
        self.addr = addr

        self.token = token

        self.send_data = self.received_data = None

        self.close_conn = False

        # Индетификационный код последнего сообщения
        self.last_vcode = ''

        # Ответ после подключения
        self.conn_resp = None

        # Запускаем новый поток, т.к asyncio.run() является
        # блокирующей функцией
        if not is_test:
            start_new_thread(self.start_async, ())
        else:
            self.start_async()

    def get_received_data(self):
        return self.received_data

    def get_conn_resp(self):
        return self.conn_resp

    def set_send_get_recv(self, data):
        # Генерируем уникальный код, который будет отвечает за определенную
        # версию
        # ВВЕДЕНО Чтобы отслеживать изменения данных, которые необходимо
        # отправить на сервер
        self.send_data = self.generate_version_code(data)
        return self.received_data

    @staticmethod
    def generate_version_code(data):
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
        # Запускаем асинхронную функцию для работы с сервером
        asyncio.run(self.start_client())

    async def start_client(self):
        try:
            async with websockets.connect(self.addr) as socket:
                # Проверяем данные, которые отправляются для регистрации
                if not self.validate_reg_data():
                    raise Exception('Токен не прошел валидацию')
                await socket.send(json.dumps(self.pi_data))

                # Ответ об успешном подключении
                self.conn_resp = json.loads(await socket.recv())
                print(self.conn_resp)

                # Если не удалось подключиться к серверу, выдаем ошибку
                if self.conn_resp['answer'] != 'Successful registration':
                    raise Exception(self.conn_resp['answer'])

                # Начинаем общаться с сервером
                async for message in socket:
                    self.received_data = json.loads(message)
                    print(self.received_data)

                    if self.received_data['answer'] == 'Start sharing':
                        # Главный цикл, который отправляет данные на сервер
                        while not self.close_conn:
                            # Если данные обновились,
                            # то отправляем их на сервер
                            if self.send_data is not None and \
                                    self.last_vcode != self.send_data['vcode']:
                                self.last_vcode = self.send_data['vcode']

                                await socket.send(json.dumps(
                                    {'status': 'sharing',
                                     'data': self.send_data}))

                            # Играем в пинг-понг, чтобы поддерживать
                            # соединение с сервером
                            pong_waiter = await socket.ping()
                            await pong_waiter
                            pong_waiter.result()

                        # Закрываем соединение с сервером
                        await socket.send(
                            json.dumps({'status': 'Close connection'}))
                        break

                    elif self.received_data['answer'] == \
                            'Pair has been established':
                        await socket.send(json.dumps(
                            {'status': 'I am ready to get'}))

                    elif self.received_data['answer'] == 'sharing':
                        print('received_data', self.received_data['data'])
                    else:
                        # Если пришли какие-то другие команлы, то выдаем ошибку
                        raise Exception(self.received_data['answer'])
        except Exception as e:
            self.exceptionSignal.emit(str(e))
            print('exc in network:', e)
        finally:
            self.close_conn = True

    def disconnect(self):
        self.close_conn = True


if __name__ == '__main__':
    net = Network(QObject(), 'ws://localhost:8080', 123, is_test=True)
