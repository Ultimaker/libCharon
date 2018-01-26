# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.

import os.path #To get the file extension from a path.

from .FileInterface import FileInterface #The interface we're implementing.

#The supported file types.
from .filetypes.UltimakerContainerFile import UltimakerContainerFile

##  A facade for a file object.
#
#   This facade finds the correct implementation based on the MIME type of the
#   file it needs to open.
class VirtualFile(FileInterface):
    def __init__(self):
        self._implementation = None

    def open(self, path, *args, **kwargs):
        _, extension = os.path.splitext(path)
        if extension == ".ufp": #TODO: Register file types dynamically.
            self._implementation = UltimakerContainerFile()
            return self._implementation.open(path, *args, **kwargs)
        raise IOError("Unknown extension {extension}.".format(extension = extension))

    def close(self, *args, **kwargs):
        if not self.__implementation:
            raise IOError("Can't close a file before it's opened.")
        result = self._implementation.close(*args, **kwargs)
        self._implementation = None #You have to open a file again, which might need a different implementation.
        return result

    ##  Causes all calls to functions that aren't defined in this class to be
    #   passed through to the implementation.
    def __getattribute__(self, item):
        if item == "open" or item == "close" or item == "__del__" or item == "_implementation": #Attributes that VirtualFile overwrites should be called normally.
            return object.__getattribute__(self, item)
        if not object.__getattribute__(self, "_implementation"):
            raise IOError("Can't use '{attribute}' before a file is opened.".format(attribute = item))
        return getattr(self._implementation, item)

    ##  When the object is deleted, close the file.
    def __del__(self):
        self.close()