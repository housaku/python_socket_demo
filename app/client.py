import socket
import time


class BaseClient:
    skt: socket.socket
    buffer_size: int

    def __init__(self, family: int, typ: int, proto: int = 0, timeout: int = 10, buffer_size: int = 1024) -> None:
        self.skt = socket.socket(family, typ, proto)
        self.skt.settimeout(timeout)
        self.buffer_size = buffer_size

    def connect(self, host: str, port: int) -> bool:
        print(f"connecting to {(host, port)}")
        try:
            self.skt.connect((host, port))
        except Exception as ex:
            print(ex)
            return False
        return True

    def send(self, message: str) -> None:
        if not message:
            print("exit for no message.")
            return
        self.skt.send(message.encode("utf-8"))
        recv_bytes = self.skt.recv(self.buffer_size)
        self.received(recv_bytes)

    def received(self, recv_bytes: bytes) -> None:
        print(f"received message: {recv_bytes.decode('utf-8')}")

    def close(self) -> None:
        try:
            self.skt.shutdown(socket.SHUT_RDWR)
            self.skt.close()
        except Exception as ex:
            print(ex)


if __name__ == "__main__":
    client = BaseClient(socket.AF_INET, socket.SOCK_STREAM)
    # 接続
    while True:
        if client.connect("127.0.0.1", 8080):
            break  # 接続成功したら抜ける
        time.sleep(5)
    # メッセージ送信
    while True:
        message = input("> ")
        if not message:
            break
        client.send(message)
    client.close()
    print("disconnect from server.")
