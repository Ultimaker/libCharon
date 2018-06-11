# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.
from collections import OrderedDict
from typing import List

from Charon.filetypes.OpenPackagingConvention import OpenPackagingConvention


##  A container file that contains Cura resources that belong together.
#   Cura can install these packages to extend the program with user generated content.
#   Examples are Cura plugins or a set of material and quality profiles.
class CuraPackage(OpenPackagingConvention):

    global_metadata_file = "/Metadata/package.json"
    metadata_relationship_type = "http://schemas.ultimaker.org/package/2018/relationships/curapackage_metadata"
    mime_type = "application/x-curapackage"

    # File aliases for quick and easy access.
    aliases = OrderedDict([
        (r"/materials", "/files/resources/materials")
    ])

    ##  Gets a list of paths to material files in the package.
    def getMaterials(self) -> List[str]:
        return self.listPaths("/materials")

    ##  Add a new material file.
    #   \param material_data The data of the material file in bytes.
    #   \param package_filename The filename to write the data to inside the package.
    def addMaterial(self, material_data: bytes, package_filename: str) -> None:
        material_path_alias = "/materials"
        self._ensureRelationExists(virtual_path=material_path_alias, relation_type="material", origin="/package.json")
        self._writeToAlias(material_path_alias, package_filename, material_data)
