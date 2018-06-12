# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.


##  A container file type that contains multiple 3D-printing related files that belong together.
from collections import OrderedDict
from io import TextIOWrapper

from Charon.OpenMode import OpenMode
from Charon.filetypes.GCodeFile import GCodeFile
from Charon.filetypes.OpenPackagingConvention import OpenPackagingConvention


class UltimakerFormatPackage(OpenPackagingConvention):

    # Where the global metadata file is.
    global_metadata_file = "/Metadata/UFP_Global.json"

    # Unique identifier of the relationship type that relates UFP metadata to files.
    metadata_relationship_type = "http://schemas.ultimaker.org/package/2018/relationships/ufp_metadata"

    # Virtual path aliases. Keys are regex. Order matters!
    aliases = OrderedDict([
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
            try:
                # Check if the G-code file actually exists in the package.
                self.zipfile.getinfo("/3D/model.gcode")
            except KeyError:
                return

            gcode_stream = TextIOWrapper(self.zipfile.open("/3D/model.gcode"))
            header_data = GCodeFile.parseHeader(gcode_stream, prefix="/3D/model.gcode/")
            self.metadata.update(header_data)
