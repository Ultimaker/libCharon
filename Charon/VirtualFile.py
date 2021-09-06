# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.
import os

from Charon.FileInterface import FileInterface  # The interface we're implementing.
from Charon.OpenMode import OpenMode  #To open local files with the selected open mode.
# The supported file types.
from Charon.filetypes.UltimakerFormatPackage import UltimakerFormatPackage
from Charon.filetypes.GCodeFile import GCodeFile
from Charon.filetypes.GCodeGzFile import GCodeGzFile
from Charon.filetypes.GCodeSocket import GCodeSocket

extension_to_mime = {
    ".ufp": "application/x-ufp",
    ".gcode": "text/x-gcode",
    ".gz": "text/x-gcode-gz",
    ".gcode.gz": "text/x-gcode-gz",
    ".gsock": "text/x-gcode-socket"
}

mime_to_implementation = {
    "application/x-ufp": UltimakerFormatPackage,
    "text/x-gcode": GCodeFile,
    "text/x-gcode-gz": GCodeGzFile,
    "text/x-gcode-socket": GCodeSocket
}


##  A facade for a file object.
#
#   This facade finds the correct implementation based on the MIME type of the
#   file it needs to open.
class VirtualFile(FileInterface):
    def __init__(self):
        self._implementation = None

    def open(self, path, mode = OpenMode.ReadOnly, *args, **kwargs):
        _, extension = os.path.splitext(path)
        if extension not in extension_to_mime:
            raise IOError("Unknown extension \"{extension}\".".format(extension = extension))
        mime = extension_to_mime[extension]
        implementation = mime_to_implementation[mime]
        return self.openStream(implementation.stream_handler(path, mode.value + "b"), mime, mode, *args, **kwargs)

    def openStream(self, stream, mime, mode = OpenMode.ReadOnly, *args, **kwargs):
        self._implementation = mime_to_implementation[mime]()
        return self._implementation.openStream(stream, mime, mode, *args, **kwargs)

    def close(self, *args, **kwargs):
        if self._implementation is None:
            raise IOError("Can't close a file before it's opened.")
        result = self._implementation.close(*args, **kwargs)
        self._implementation = None  # You have to open a file again, which might need a different implementation.
        return result

    ##  Causes all calls to functions that aren't defined in this class to be
    #   passed through to the implementation.
    def __getattribute__(self, item):
        if item == "open" or item == "openStream" or item == "close" or item == "__del__" or item == "_implementation":
            # Attributes that VirtualFile overwrites should be called normally.
            return object.__getattribute__(self, item)
        if not object.__getattribute__(self, "_implementation"):
            raise IOError("Can't use '{attribute}' before a file is opened.".format(attribute = item))
        return getattr(self._implementation, item)

    ##  When the object is deleted, close the file.
    def __del__(self):
        if self._implementation is not None:
            self.close()
