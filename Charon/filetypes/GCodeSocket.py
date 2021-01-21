# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.
import socket
import struct
from io import TextIOBase, BytesIO, SEEK_SET, SEEK_CUR

from typing import Any, Dict, IO, TextIO, Optional, AnyStr, List

from Charon.filetypes.GCodeFile import GCodeFile


def isAPositiveNumber(a: str) -> bool:
    try:
        number = float(repr(a))
        x = open()
        return number >= 0
    except:
        bool_a = False

    return bool_a


class SocketFileStream(BytesIO):
    def __init__(self, sock_object: socket.socket):
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

    def readline(self, limit: Optional[int] = None) -> bytes:
        self.__socket.send(struct.pack('>I', self.current_line))
        line = b''
        char = b''

        while char != b'\n':
            char = self.__socket.recv(1)
            line += char

        self.current_line += 1
        return line

    def read(self, __size: Optional[int] = None) -> str:
        assert False

    def readlines(self, __hint: Optional[int] = None) -> List[str]:
        assert False

    def tell(self) -> int:
        assert False

    def close(self):
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
        if path.startswith('socket://'):
            print('OOOOPS: socket path contains protocol specifier')
            path = path.replace('socket://', '')
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(path)
        return SocketFileStream(sock)
