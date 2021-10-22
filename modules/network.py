import json
import random
import signal
import socket
import string
import asyncio
from _thread import start_new_thread

import websockets
from threading import Thread

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

        self.websocket = None

        self.loop = self.task = self.thread = None

        # Запускаем новый поток, т.к asyncio.run() является
        # блокирующей функцией
        # self.start_async()
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
        # # Запускаем асинхронную функцию для работы с сервером
        # self.loop = asyncio.new_event_loop()
        # #
        # # asyncio.set_event_loop(self.loop)
        # #
        # self.task = self.loop.create_task(self.start_client())
        # self.thread = Thread(target=self.loop.run_forever)
        # self.thread.start()
        # # self.loop.run_until_complete(asyncio.wait([self.task]))
        asyncio.run(self.start_client())

    async def start_client(self):
        print('Started')
        try:
            async with websockets.connect(self.addr) as websocket:
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
                # while not self.close_conn:
                #     await asyncio.sleep(1)
                #
                # Начинаем общаться с сервером
                while True:
                    print('opened')
                    if self.close_conn:
                        print('disconnected')
                        await websocket.send(
                            json.dumps({'status': 'Close connection'}))
                        break
                    try:
                        self.received_data = json.loads(
                            await asyncio.wait_for(
                                websocket.recv(), timeout=1.0))
                    except asyncio.TimeoutError:
                        print('excp')
                        continue
                    print(self.received_data)

                    if self.received_data['answer'] == 'Start sharing':
                        # Главный цикл, который отправляет данные на сервер
                        while not self.close_conn:
                            print(self.close_conn)
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
                    elif 'answer' in self.received_data:
                        # Если пришли какие-то другие команлы, то выдаем ошибку
                        raise Exception(self.received_data['answer'])
        except Exception as e:
            self.exceptionSignal.emit(self.validate_exception(e))
            print('exc in network:', e)
        finally:
            self.close_conn = True

    def disconnect(self):
        self.close_conn = True
        # future = asyncio.run_coroutine_threadsafe(
        #     self.loop.create_task(self.websocket.close()).get_coro(), self.loop)

        # print(self.task.cancelled())
        # self.loop.call_soon_threadsafe(self.task.cancel)
        # self.loop.call_soon_threadsafe(self.loop.stop)
        # self.loop.call_soon_threadsafe(self.loop.close)
        # self.loop.call_soon_threadsafe(self.websocket.close)
        # print(self.task.cancelled())
        # # self.task.cancel()
        # # self.loop.close()
        # self.thread.join()
        # # print(self.task.cancelled())
        # print(self.thread, self.loop, self.task)
        # print(self.thread.is_alive())


    @staticmethod
    def validate_exception(exc):
        try:
            raise exc
        except (ConnectionRefusedError, socket.gaierror) as e:
            return 'Проверьте состояние интернета и попробуйте снова.'
        except Exception as e:
            return str(e)


if __name__ == '__main__':
    net = Network(QObject(), 'ws://localhost:8080', 1234, is_test=True)
