import asyncio
import socket
import sys


class AsyncServer:
    skt: socket.socket
    buffer_size: int
    is_running: bool = True
    is_sending: bool = True

    def __init__(self, family: int, typ: int, proto: int = 0, timeout: int = 30, buffer_size: int = 1024):
        self.skt = socket.socket(family, typ, proto)
        self.skt.settimeout(timeout)
        self.skt.setblocking(False)  # none blocking
        self.buffer_size = buffer_size

    # def __del__(self) -> None:
    #     self.close()

    def listen(self, address: str, port: int) -> None:
        self.skt.bind((address, port))
        self.skt.listen(1)
        print(f"Server listening on {(address, port)}... ")

    async def run_async(self) -> None:
        loop = asyncio.get_event_loop()
        asyncio.create_task(self.handle_control(loop))
        # asyncio event loop
        while self.is_running:
            client, cli_addr = await loop.sock_accept(self.skt)
            client.setblocking(False)  # none blocking
            print(f"Server accepted client: {cli_addr}")
            asyncio.create_task(self.handle_recv(client, loop))
            asyncio.create_task(self.handle_send(client, loop))
        loop.close()

    async def handle_control(self, loop: asyncio.AbstractEventLoop) -> None:
        """ユーザからの入力を受けるタスク"""
        while True:
            line = await input_async("")
            if not line:
                continue
            elif line in ["h", "help"]:
                print('"h" or "help": print this help massage.')
                print('"q" or "quit": quit server.')
                print('"s" or "send": toggle send flag.')
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

    async def handle_send(self, client: socket.socket, loop: asyncio.AbstractEventLoop) -> None:
        """送信処理を行うタスク"""
        while True:
            await asyncio.sleep(5)
            if self.is_sending:
                try:
                    message = "send from server!"
                    await loop.sock_sendall(client, message.encode("utf-8"))
                    print(f"TX: {message}")
                except ConnectionResetError:
                    # 接続が切れているので送信を終了する
                    print("disconnected from client!")
                    return
                except Exception as ex:
                    print(f"catch Exception: {ex}")
                    break

    async def handle_recv(self, client: socket.socket, loop: asyncio.AbstractEventLoop) -> None:
        """受信処理を行うタスク"""
        while True:
            try:
                recv_bytes = await loop.sock_recv(client, self.buffer_size)
                resp_bytes = self.respond(recv_bytes)
                await loop.sock_sendall(client, resp_bytes)
                print(f"TX: {resp_bytes.decode('utf-8')}")
            except ConnectionAbortedError:
                print("disconnected from client!")
                break
            except Exception as ex:
                print(f"catch Exception: {ex}")
                break

    def respond(self, recv_bytes: bytes) -> bytes:
        """応答処理"""
        print(f"RX: {recv_bytes.decode('utf-8')}")
        return "Server accepted.".encode("utf-8")

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
    server = AsyncServer(socket.AF_INET, socket.SOCK_STREAM)
    server.listen("0.0.0.0", 8080)
    await server.run_async()
    print("server shutdown!")


if __name__ == "__main__":
    asyncio.run(main())
