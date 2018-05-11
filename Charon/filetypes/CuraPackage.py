# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.
from collections import OrderedDict
from typing import List

from Charon.filetypes.OpenPackagingConvention import OpenPackagingConvention


class CuraPackage(OpenPackagingConvention):
    """
    A container file that contains Cura resources that belong together.
    For example a machine definition with several materials and quality profiles.
    """

    # Some constants related to this format.
    global_metadata_file = "/Metadata/package.json"
    metadata_relationship_type = "http://schemas.ultimaker.org/package/2018/relationships/curapackage_metadata"
    mime_type = "application/x-curapackage"
    
    # File aliases for quick and easy access.
    aliases = OrderedDict([
        (r"/materials", "/files/resources/materials")
    ])

    def getMaterials(self) -> List[str]:
        """
        Get all material files.
        :return: A list of paths of materials.
        """
        return self.listPaths("/materials")

    def getQualities(self) -> List[str]:
        """
        Get all quality files.
        :return: A list of paths of qualities.
        """
        return self.listPaths("/qualities")
