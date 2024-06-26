import asyncio
import sys

# asyncio.start_serverを利用したechoサーバ
# Streamを使ってシンプルに書けますが、複数クライアントへの対応がうまく動作しない問題があります。


class AsyncServer:
    buffer_size: int
    is_running: bool = True
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
        tx_buffers: list[str] = []
        asyncio.create_task(self.handle_recv(reader, tx_buffers))
        asyncio.create_task(self.handle_send(writer, tx_buffers))
        asyncio.create_task(self.handle_cycle(tx_buffers))

    async def handle_cycle(self, tx_buffers: list[str]) -> None:
        count = 0
        while self.is_running:
            await asyncio.sleep(1.0)
            count += 1
            if count % 10 == 0:
                message = f"{count} seconds have passed since server connection."
                tx_buffers.append(message)

    async def handle_send(self, writer: asyncio.StreamWriter, tx_buffers: list[str]) -> None:
        """送信処理を行うタスク"""
        while self.is_running:
            await asyncio.sleep(0.2)
            if tx_buffers:
                try:
                    message = tx_buffers.pop(0)
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

    async def handle_recv(self, reader: asyncio.StreamReader, tx_buffers: list[str]) -> None:
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
                self.respond(recv_bytes, tx_buffers)
            else:
                print("disconnected from client!!!")
                self.close()
                return

    def respond(self, recv_bytes: bytes, tx_buffers: list[str]) -> None:
        """応答処理"""
        print(f"RX: {recv_bytes.decode('utf-8')}")
        message = f"echo {recv_bytes.decode('utf-8')!r}"
        tx_buffers.append(message)

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
    await AsyncServer().run_async("0.0.0.0", 8080)
    print("server shutdown!")


asyncio.run(main())
