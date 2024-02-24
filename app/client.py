import asyncio
import socket
import sys


class AsyncClient:
    skt: socket.socket
    buffer_size: int
    is_running: bool = True
    is_sending: bool = True

    def __init__(self, family: int, typ: int, proto: int = 0, timeout: int = 10, buffer_size: int = 1024) -> None:
        self.skt = socket.socket(family, typ, proto)
        self.skt.settimeout(timeout)
        self.skt.setblocking(False)  # none blocking
        self.buffer_size = buffer_size

    async def connect_async(self, host: str, port: int) -> None:
        loop = asyncio.get_event_loop()
        # 制御 処理
        asyncio.create_task(self.handle_control(loop))
        # 接続
        print(f"connecting to {(host, port)}...")
        while self.is_running:
            try:
                await asyncio.wait_for(loop.sock_connect(self.skt, (host, port)), timeout=1.0)
                break
            except asyncio.TimeoutError:
                continue
        print("connecting success!")
        # 送信/受信 処理
        asyncio.create_task(self.handle_recv(self.skt, loop))
        asyncio.create_task(self.handle_send(self.skt, loop))
        while self.is_running:
            await asyncio.sleep(5)
        loop.close()

    async def handle_control(self, loop: asyncio.AbstractEventLoop) -> None:
        while self.is_running:
            line = await input_async("")
            if not line:
                continue
            elif line in ["q", "quit"]:
                self.is_running = False
                loop.stop()
            elif line in ["s", "send"]:
                self.is_sending ^= True
                if self.is_sending:
                    print("send flag On")
                else:
                    print("send flag off")
            else:
                print("unknown command!")

    async def handle_send(self, skt: socket.socket, loop: asyncio.AbstractEventLoop) -> None:
        while self.is_running:
            await asyncio.sleep(5)
            if self.is_sending:
                try:
                    message = "send from client!"
                    await loop.sock_sendall(skt, message.encode("utf-8"))
                    print(f"TX: {message}")
                except ConnectionResetError:
                    # 接続が切れているので送信を終了する
                    print("disconnected from server!")
                    return
                except Exception as ex:
                    print(f"catch Exception: {ex}")
                    break

    async def handle_recv(self, skt: socket.socket, loop: asyncio.AbstractEventLoop) -> None:
        while self.is_running:
            try:
                recv_bytes = await loop.sock_recv(skt, self.buffer_size)
                self.respond(recv_bytes)
            except ConnectionAbortedError:
                print("disconnected from server!")
                break
            except Exception as ex:
                print(f"catch Exception: {ex}")
                break

    def respond(self, recv_bytes: bytes) -> None:
        """応答処理 (表示のみ)"""
        if 0 < len(recv_bytes):
            print(f"RX: {recv_bytes.decode('utf-8')}")

    def close(self) -> None:
        try:
            self.skt.shutdown(socket.SHUT_RDWR)
            self.skt.close()
        except Exception as ex:
            print(ex)


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
