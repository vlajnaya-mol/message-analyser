import asyncio
from message_analyser.GUI import start_gui


if __name__ == "__main__":
    aio_loop = asyncio.get_event_loop()
    try:
        aio_loop.run_until_complete(start_gui(aio_loop))
    finally:
        if not aio_loop.is_closed():
            aio_loop.close()