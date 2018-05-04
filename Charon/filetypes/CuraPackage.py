# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.
from collections import OrderedDict
from Charon.filetypes.OpenDocumentFormat import OpenDocumentFormat


class CuraPackage(OpenDocumentFormat):
    """
    A container file that contains Cura resources that belong together.
    For example a machine definition with several materials and quality profiles.
    """
    
    # Some constants related to this format.
    global_metadata_file = "/Metadata/CuraPackage_Global.json"
    metadata_relationship_type = "http://schemas.ultimaker.org/package/2018/relationships/curapackage_metadata"
    aliases = OrderedDict([])
    mime_type = "application/x-curapackage"
