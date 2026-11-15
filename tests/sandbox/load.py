"""A program that loads a container, to prove the guarantees of a run by what they stop.

It runs inside the container as `python /dokime/project/load.py <what>`, and writes what it
measured to `/dokime/out/result`. The tests copy it into the project they mount.
"""

import os
import socket
import sys
import threading
import time
from pathlib import Path

RESULT = Path("/dokime/out/result")
MIB = 1024 * 1024


def network() -> str:
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=3).close()
    except OSError as error:
        return f"refused {type(error).__name__}"
    return "connected"


def memory(megabytes: int) -> str:
    blocks = []
    for _ in range(megabytes // 50):
        block = bytearray(50 * MIB)
        block[:: os.sysconf("SC_PAGE_SIZE")] = b"\x01" * len(
            range(0, len(block), os.sysconf("SC_PAGE_SIZE"))
        )
        blocks.append(block)
    return f"allocated {len(blocks) * 50}"


def processes(wanted: int) -> str:
    started = 0
    for _ in range(wanted):
        try:
            threading.Thread(target=time.sleep, args=(5,), daemon=True).start()
        except RuntimeError:
            break
        started += 1
    return f"started {started}"


def processor(workers: int, seconds: float) -> str:
    begin = time.monotonic()
    children = []
    for _ in range(workers):
        child = os.fork()
        if child == 0:
            while time.monotonic() - begin < seconds:
                pass
            os._exit(0)
        children.append(child)
    for child in children:
        os.waitpid(child, 0)
    wall = time.monotonic() - begin
    used = os.times().children_user + os.times().children_system
    return f"ratio {used / wall:.3f}"


def write(path: str) -> str:
    try:
        Path(path).write_text("written\n")
    except OSError as error:
        return f"refused {type(error).__name__}"
    return "written"


def main(what: str, *args: str) -> None:
    actions = {
        "network": lambda: network(),
        "memory": lambda: memory(int(args[0])),
        "processes": lambda: processes(int(args[0])),
        "processor": lambda: processor(int(args[0]), float(args[1])),
        "write": lambda: write(args[0]),
    }
    RESULT.write_text(actions[what]())


if __name__ == "__main__":
    main(*sys.argv[1:])
