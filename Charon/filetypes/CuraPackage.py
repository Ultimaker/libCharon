# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.

from collections import OrderedDict  # To specify the aliases in order.
from Charon.filetypes.OpenDocumentFormat import OpenDocumentFormat


##  A container file type that contains multiple 3D-printing related files that
#   belong together.
class CuraPackage(OpenDocumentFormat):
    
    # Some constants related to this format.
    global_metadata_file = "/Metadata/CuraPackage_Global.json"  # Where the global metadata file is.
    metadata_relationship_type = "http://schemas.ultimaker.org/package/2018/relationships/curapackage_metadata"  # Unique identifier of the relationship type that relates CuraPackage metadata to files.
    aliases = OrderedDict([])  # Virtual path aliases. Keys are regex. Order matters!
    mime_type = "application/x-curapackage"
    
    ##  Initialises the fields of this class.
    def __init__(self):
        super().__init__()
