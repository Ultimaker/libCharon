# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.
from collections import OrderedDict
from typing import List

from Charon.filetypes.OpenPackagingConvention import OpenPackagingConvention, OPCError


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

    def addMaterial(self, material_data: bytes, package_filename: str) -> None:
        """
        Add a new material file.
        :param material_data: The data that should  be in the material file as bytes.
        :param package_filename: The filename in the package to write the data to.
        """
        material_path_alias = "/materials"
        self._ensureRelationExists(virtual_path=material_path_alias, relation_type="material", origin="/package.json")
        self._writeToAlias(material_path_alias, package_filename, material_data)

    def getQualities(self) -> List[str]:
        """
        Get all quality files.
        :return: A list of paths of qualities.
        """
        return self.listPaths("/qualities")

    def _writeToAlias(self, path_alias: str, package_filename: str, file_data: bytes) -> None:
        """
        Write file data to a given path alias and filename.
        """
        material_stream = self.getStream("{}/{}".format(path_alias, package_filename))
        material_stream.write(file_data)

    def _ensureRelationExists(self, virtual_path: str, relation_type: str, origin: str) -> None:
        """
        Ensure a relation exists.
        """
        try:
            # We try to add the relation. If this throws an OPCError, we know the relation already exists and ignore it.
            self.addRelation(virtual_path=virtual_path, relation_type=relation_type, origin=origin)
        except OPCError:
            pass
