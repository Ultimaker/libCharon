# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.
from collections import OrderedDict
from typing import List

from Charon.OpenMode import OpenMode
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
        (r"/materials", "/files/resources/materials"),
        (r"/qualities", "/files/resources/qualities"),
        (r"/machines", "/files/resources/machines")
    ])

    ##  Gets a list of paths to material files in the package.
    def getMaterials(self) -> List[str]:
        return self.listPaths("/materials")

    ##  Add a new material file.
    #   \param material_data The data of the material file in bytes.
    #   \param package_filename The location to write the data to inside the package.
    def addMaterial(self, material_data: bytes, package_filename: str) -> None:
        material_path_alias = "/materials"
        self._ensureRelationExists(virtual_path=material_path_alias, relation_type="material", origin="/package.json")
        self._writeToAlias(material_path_alias, package_filename, material_data)

    ##  Gets a list of paths to quality files in the package.
    def getQualities(self) -> List[str]:
        return self.listPaths("/qualities")

    ##  Add a new quality file.
    #   \param: quality_data The data of the quality file in bytes.
    #   \param package_filename The location to write the data to inside the package.
    def addQuality(self, quality_data: bytes, package_filename: str) -> None:
        quality_path_alias = "/qualities"
        self._ensureRelationExists(virtual_path=quality_path_alias, relation_type="quality", origin="/package.json")
        self._writeToAlias(quality_path_alias, package_filename, quality_data)

    ##  Gets a list of paths to machine definition files in the package.
    def getMachines(self) -> List[str]:
        return self.listPaths("/machines")

    ##  Add a new machine definition file.
    #   \param: machine_data The data of the machine definition file in bytes.
    #   \param package_filename The location to write the data to inside the package.
    def addMachine(self, machine_data: bytes, package_filename: str) -> None:
        machine_path_alias = "/machines"
        self._ensureRelationExists(virtual_path=machine_path_alias, relation_type="machine", origin="/package.json")
        self._writeToAlias(machine_path_alias, package_filename, machine_data)

    ##  Export the package to bytes.
    def toByteArray(self, offset: int = 0, count: int = -1) -> bytes:
        self._validateMetadata()
        return super().toByteArray(offset, count)

    ##  Creates all the required content types for a .curapackage.
    def _readContentTypes(self):
        super()._readContentTypes()
        if self.mode != OpenMode.ReadOnly:
            self.addContentType(extension="xml.fdm_material", mime_type="application/x-ultimaker-material-profile")
            self.addContentType(extension="inst.cfg", mime_type="application/x-ultimaker-quality-profile")

    ##  Validates if the package.json metadata file contains all the required keys
    #   and if they are in the correct format.
    def _validateMetadata(self):
        # TODO
        pass
