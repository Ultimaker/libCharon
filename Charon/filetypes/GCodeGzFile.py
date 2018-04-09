from Charon.filetypes.GCodeFile import GCodeFile
import gzip


class GCodeGzFile(GCodeFile):
    stream_handler = gzip.open
    mime_type = "text/x-gcode-gz"

    def __init__(self):
        super().__init__()