import asyncio
import socket
import sys


# https://stackoverflow.com/questions/58454190/python-async-waiting-for-stdin-input-while-doing-other-stuff
async def input_async(string: str) -> str:
    await asyncio.to_thread(sys.stdout.write, f"{string} ")
    return (await asyncio.to_thread(sys.stdin.readline)).rstrip("\n")


async def handle_send(client: socket.socket, loop: asyncio.AbstractEventLoop) -> None:
    while True:
        message = await input_async("> ")
        if not message:
            break
        await loop.sock_sendall(client, message.encode("utf-8"))


async def handle_recv(client: socket.socket, loop: asyncio.AbstractEventLoop) -> None:
    while data := await loop.sock_recv(client, 1024):
        print(f"data = {data.decode('ascii')}")
        await loop.sock_sendall(client, data)
    client.close()


async def run_server() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(False)
    server.bind(("localhost", 8000))
    server.listen()
    loop = asyncio.get_event_loop()

    while True:
        conn, address = await loop.sock_accept(server)
        conn.setblocking(False)
        print(f"New client from {address}")
        asyncio.create_task(handle_recv(conn, loop))
        asyncio.create_task(handle_send(conn, loop))


if __name__ == "__main__":
    asyncio.run(run_server())
