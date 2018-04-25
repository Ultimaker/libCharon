# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.

from collections import OrderedDict  # To specify the aliases in order.
from io import TextIOWrapper  # For the type of input of openStream and to create binary output streams for getting metadata.

from Charon.filetypes.OpenDocumentFormat import OpenDocumentFormat
from Charon.OpenMode import OpenMode  # To detect whether we want to read and/or write to the file.
from Charon.filetypes.GCodeFile import GCodeFile  # Required for fallback G-Code header parsing.


##  A container file type that contains multiple 3D-printing related files that
#   belong together.
class UltimakerFormatPackage(OpenDocumentFormat):
    
    # Some constants related to this format.
    global_metadata_file = "/Metadata/UFP_Global.json"  # Where the global metadata file is.
    metadata_relationship_type = "http://schemas.ultimaker.org/package/2018/relationships/ufp_metadata"  # Unique identifier of the relationship type that relates UFP metadata to files.
    aliases = OrderedDict([  # Virtual path aliases. Keys are regex. Order matters!
        (r"^/preview/default", "/Metadata/thumbnail.png"),
        (r"^/preview", "/Metadata/thumbnail.png"),
        (r"^/toolpath/default", "/3D/model.gcode"),
        (r"^/toolpath", "/3D/model.gcode"),
    ])
    mime_type = "application/x-ufp"

    ##  Initialises the fields of this class.
    def __init__(self):
        super().__init__()
    
    ##  When loading a file, read its metadata from the archive.
    #
    #   This depends on the relations! Read the relations first!
    def _readMetadata(self) -> None:
        super()._readMetadata()
        if self.mode != OpenMode.WriteOnly and not self.getMetadata("/3D/model.gcode"):
            if "/3D/model.gcode" in [member.filename for member in self.zipfile.infolist()]:
                gcode_stream = TextIOWrapper(self.zipfile.open("/3D/model.gcode"))
                header_data = GCodeFile.parseHeader(gcode_stream, prefix = "/3D/model.gcode/")
                self.metadata.update(header_data)
