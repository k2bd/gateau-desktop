import os

#: Port for socket communication with the emulator, default 55722
GATEAU_SOCKET_PORT = os.environ.get("GATEAU_SOCKET_PORT", 55722)
