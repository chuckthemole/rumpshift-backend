import socket
import threading
from arduino_client.protocols import encode_message


class ArduinoClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.lock = threading.Lock()
        self.sock = None
        self.connect()

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port))
        # Optional: set timeouts or wrap with a file-like object

    def send_command(self, command: str, payload: dict):
        msg = encode_message(command, payload)
        with self.lock:
            self.sock.sendall(msg)

    def close(self):
        if self.sock:
            self.sock.close()
