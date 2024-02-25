import asyncio
import socket
import sys


class AsyncClient:
    skt: socket.socket
    buffer_size: int
    is_running: bool = True
    send_list: list[str] = []

    def __init__(self, family: int, typ: int, proto: int = 0, timeout: int = 10, buffer_size: int = 1024) -> None:
        self.skt = socket.socket(family, typ, proto)
        self.skt.settimeout(timeout)
        self.skt.setblocking(False)  # none blocking
        self.buffer_size = buffer_size

    async def connect_async(self, host: str, port: int) -> None:
        # 制御 処理
        asyncio.create_task(self.handle_control())
        # 接続
        print(f"connecting to {(host, port)}...")
        while self.is_running:
            try:
                reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=1.0)
                break
            except asyncio.TimeoutError:
                continue
        print("connecting success!")
        # 送信/受信 処理
        await asyncio.gather(
            asyncio.create_task(self.handle_recv(reader)),
            asyncio.create_task(self.handle_send(writer)),
        )

    async def handle_control(self) -> None:
        """ユーザからの入力を受けるタスク"""
        while self.is_running:
            line = await input_async("")
            if not line:
                continue
            elif line in ["q", "quit"]:
                self.close()
            elif line in ["h", "help"]:
                print('"q" or "quit": quit client.')
                print('"h" or "help": print this help massage.')
                print("other        : send input text to server.")
            else:
                self.send_list.append(line)

    async def handle_send(self, writer: asyncio.StreamWriter) -> None:
        """送信処理を行うタスク"""
        while self.is_running:
            await asyncio.sleep(0.2)
            if self.send_list:
                try:
                    message = self.send_list.pop()
                    writer.write(message.encode("utf-8"))
                    await writer.drain()
                    print(f"TX: {message}")
                except ConnectionResetError:
                    # 接続が切れているので送信を終了する
                    print("disconnected from server!")
                    return
                except Exception as ex:
                    print(f"catch Exception: {ex}")
                    break
        writer.close()
        await writer.wait_closed()

    async def handle_recv(self, reader: asyncio.StreamReader) -> None:
        """受信処理を行うタスク"""
        while self.is_running:
            try:
                recv_bytes = await reader.read(self.buffer_size)
            except ConnectionAbortedError:
                print("disconnected from server!!")
                break
            except Exception as ex:
                print(f"catch Exception: {ex}")
                break
            # サーバ側が落ちるとなぜか空電文が届くので終了する
            if 0 < len(recv_bytes):
                self.respond(recv_bytes)
            else:
                print("disconnected from server!!!")
                self.close()
                return

    def respond(self, recv_bytes: bytes) -> None:
        """応答処理 (表示のみ)"""
        print(f"RX: {recv_bytes.decode('utf-8')}")

    def close(self) -> None:
        try:
            # if self.skt:
            #     self.skt.shutdown(socket.SHUT_RDWR)
            #     self.skt.close()
            self.is_running = False
        except Exception as ex:
            print(f"catch Exception: {ex}")


# https://stackoverflow.com/questions/58454190/python-async-waiting-for-stdin-input-while-doing-other-stuff
async def input_async(string: str) -> str:
    """非同期向けのinput()"""
    await asyncio.to_thread(sys.stdout.write, f"{string}")
    return (await asyncio.to_thread(sys.stdin.readline)).rstrip("\n")


async def main() -> None:
    client = AsyncClient(socket.AF_INET, socket.SOCK_STREAM)
    await client.connect_async("127.0.0.1", 8080)
    print("client shutdown!")


if __name__ == "__main__":
    asyncio.run(main())
