# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.
import gzip

from Charon.filetypes.GCodeFile import GCodeFile


class GCodeGzFile(GCodeFile):
    stream_handler = gzip.open
    mime_type = "text/x-gcode-gz"

    def __init__(self) -> None:
        super().__init__()
