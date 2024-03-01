import asyncio
import sys

# asyncio.start_serverを利用したechoサーバ
# Streamを使ってシンプルに書けますが、複数クライアントへの対応がうまく動作しない問題があります。


class AsyncServer:
    buffer_size: int
    is_running: bool = True
    send_list: list[str] = []
    server: asyncio.Server

    def __init__(self, buffer_size: int = 1024):
        self.buffer_size = buffer_size

    async def run_async(self, host: str, port: int) -> None:
        asyncio.create_task(self.handle_control())
        print(f"Server listening on {(host, port)}... ")
        self.server = await asyncio.start_server(self.handle_echo, host, port)
        async with self.server:
            await self.server.wait_closed()

    async def handle_control(self) -> None:
        """ユーザからの入力を受けるタスク"""
        while self.is_running:
            line = await input_async("")
            if not line:
                continue
            elif line in ["h", "help"]:
                print('"h" or "help": print this help massage.')
                print('"q" or "quit": quit server.')
            elif line in ["q", "quit"]:
                self.close()
            else:
                print("unknown command!")

    async def handle_echo(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        addr = writer.get_extra_info("peername")
        print(f"Server connected client: {addr}")
        asyncio.create_task(self.handle_recv(reader))
        asyncio.create_task(self.handle_send(writer))

    async def handle_send(self, writer: asyncio.StreamWriter) -> None:
        """送信処理を行うタスク"""
        while self.is_running:
            await asyncio.sleep(0.2)
            if self.send_list:
                try:
                    message = self.send_list.pop(0)
                    writer.write(message.encode("utf-8"))
                    await writer.drain()
                    print(f"TX: {message}")
                except ConnectionResetError:
                    # 接続が切れているので送信を終了する
                    print("disconnected from client!")
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
                print("disconnected from client!!")
                break
            except Exception as ex:
                print(f"catch Exception: {ex}")
                break
            # 相手側が落ちると空電文が届くので終了する
            if 0 < len(recv_bytes):
                self.respond(recv_bytes)
            else:
                print("disconnected from client!!!")
                self.close()
                return

    def respond(self, recv_bytes: bytes) -> None:
        """応答処理"""
        print(f"RX: {recv_bytes.decode('utf-8')}")
        message = f"echo {recv_bytes.decode('utf-8')!r}"
        self.send_list.append(message)

    def close(self) -> None:
        self.is_running = False
        if self.server:
            self.server.close()


# https://stackoverflow.com/questions/58454190/python-async-waiting-for-stdin-input-while-doing-other-stuff
async def input_async(string: str) -> str:
    """非同期向けのinput()"""
    await asyncio.to_thread(sys.stdout.write, f"{string}")
    return (await asyncio.to_thread(sys.stdin.readline)).rstrip("\n")


async def main() -> None:
    # try:
    await AsyncServer().run_async("0.0.0.0", 8080)
    # except asyncio.CancelledError:
    #     print("server shutdown!")


asyncio.run(main())
