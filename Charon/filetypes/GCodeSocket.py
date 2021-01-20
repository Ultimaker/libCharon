# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.
import socket

from typing import Any, Dict, IO, TextIO, Optional

from Charon.filetypes import GCodeFile


def isAPositiveNumber(a: str) -> bool:
    try:
        number = float(repr(a))
        return number >= 0
    except:
        bool_a = False

    return bool_a


class GCodeSocket(GCodeFile):
    mime_type = "text/x-gcode-socket"

    MaximumHeaderLength = 100

    def __init__(self) -> None:
        super.__init__(self)
        self.__stream = None  # type: Optional[IO[bytes]]
        self.__metadata = {}  # type: Dict[str, Any]
        self.__sock = None

    @staticmethod
    def stream_handler(path: str) -> TextIO:
        if path.startswith('file://'):
            print('OOOOPS: socket path contains protocol specifier')
            path = path.replace('file://', '')
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(path)
        file_stream = sock.makefile('r', buffering=0)

        # Hijack readline() so we can acknowledge every line we
        # read from the socket
        old_readline = file_stream.readline

        def hacked_readline():
            line = old_readline()
            if line != "":
                sock.send(b'0x01')
            return line
        file_stream.readline = hacked_readline
        return file_stream

    def close(self) -> None:
        pass
        # assert self.__stream is not None
        #
        # self.__stream.close()
        # self.__sock.close()
