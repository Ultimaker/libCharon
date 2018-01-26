# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.

from typing import Optional
import zipfile

from ..FileInterface import FileInterface #The interface we're implementing.
from ..OpenMode import OpenMode #To detect whether we want to read and/or write to the file.

##  A container file type that contains multiple 3D-printing related files that
#   belong together.
class UltimakerContainerFile(FileInterface):
    def open(self, path: Optional[str] = None, mode: OpenMode = OpenMode.ReadOnly):
        self.mode = mode
        self.zipfile = zipfile.ZipFile(path, self.mode.value, compression = zipfile.ZIP_DEFLATED)

    def close(self):
        self.flush()
        self.zipfile.close()

    def flush(self):
        #Zipfile doesn't need flushing.
        pass

    def getStream(self, virtual_path):
        if self.mode == OpenMode.WriteOnly and virtual_path not in self.zipfile.namelist(): #File doesn't exist yet.
            self.zipfile.writestr(virtual_path, "")
            #TODO: Add manifest.

        return self.zipfile.open(virtual_path, self.mode.value)

    def toByteArray(self, offset: int = 0, count: int = -1):
        with open(self.zipfile.filename, "b") as f:
            if offset > 0:
                f.seek(offset)
            return f.read(count)