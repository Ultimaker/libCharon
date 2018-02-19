from Charon.filetypes.GCodeFile import GCodeFile
import gzip


class GCodeGzFile(GCodeFile):
    stream_handler = gzip.open

    def __init__(self):
        super().__init__()