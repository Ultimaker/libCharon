# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.

from typing import Optional
import xml.etree.ElementTree as ET #For writing XML manifest files.
import zipfile

from ..FileInterface import FileInterface #The interface we're implementing.
from ..OpenMode import OpenMode #To detect whether we want to read and/or write to the file.

##  A container file type that contains multiple 3D-printing related files that
#   belong together.
class UltimakerContainerFile(FileInterface):
    xml_header = ET.ProcessingInstruction("xml", "version=\"1.0\" encoding=\"UTF-8\"")

    def open(self, path: Optional[str] = None, mode: OpenMode = OpenMode.ReadOnly):
        self.mode = mode
        self.zipfile = zipfile.ZipFile(path, self.mode.value, compression = zipfile.ZIP_DEFLATED)
        self.relations_element = ET.Element("Relationships", xmlns = "http://schemas.openxmlformats.org/package/2006/relationships")

        #Set up an empty container.
        self.zipfile.writestr("_rels/.rels", ET.tostring(self.xml_header) + "\n" + ET.tostring(self.relations_element))

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

        if self.mode == OpenMode.WriteOnly: #Instead of appending, we want to overwrite this file completely.
            subfile_mode = "w"
        else:
            subfile_mode = self.mode.value
        return self.zipfile.open(virtual_path, subfile_mode)

    def toByteArray(self, offset: int = 0, count: int = -1):
        with open(self.zipfile.filename, "b") as f:
            if offset > 0:
                f.seek(offset)
            return f.read(count)