# Copyright (c) 2021 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.

import socket
import struct
from io import BytesIO, SEEK_SET, SEEK_CUR

from typing import Any, Dict, IO, Optional, List

from Charon.filetypes.GCodeFile import GCodeFile
from urllib.parse import urlparse


## This class is used to read GCode stream that are served
#  dynamically over a TCP connection.
class SocketFileStream(BytesIO):
    def __init__(self, sock_object: socket.socket) -> None:
        super().__init__()
        self.current_line = 0
        self.__socket = sock_object

    def seekable(self) -> bool:
        return True

    def seek(self, offset: int, whence: Optional[int] = None) -> int:
        if whence is None or whence == SEEK_SET:
            self.current_line = offset
        elif whence == SEEK_CUR:
            self.current_line += offset
        else:
            raise ValueError('Unsupported whence mode in seek: %d' % whence)
        return offset

    def readline(self, _size: int = -1) -> bytes:
        self.__socket.send(struct.pack('>I', self.current_line))
        line = b''
        char = b''

        while char != b'\n':
            char = self.__socket.recv(1)
            line += char

        self.current_line += 1
        return line

    def read(self, _size: int = -1) -> bytes:
        raise NotImplementedError("Only readline has been implemented")

    def readlines(self, _hint: int = -1) -> List[bytes]:
        raise NotImplementedError("Only readline has been implemented")

    def tell(self) -> int:
        raise NotImplementedError("Only readline has been implemented")

    def close(self) -> None:
        self.__socket.close()

    def __iter__(self):
        return self

    def __next__(self):
        return self.readline()


class GCodeSocket(GCodeFile):
    mime_type = "text/x-gcode-socket"

    MaximumHeaderLength = 100

    def __init__(self) -> None:
        super().__init__()
        self.__stream = None  # type: Optional[IO[bytes]]
        self.__metadata = {}  # type: Dict[str, Any]
        self.__sock = None

    @staticmethod
    def stream_handler(path: str, mode: str) -> IO:
        url = urlparse(path)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((url.hostname, 1337))
        return SocketFileStream(sock)
