# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.
import os
import re
from collections import OrderedDict
from typing import List

from Charon.OpenMode import OpenMode
from Charon.filetypes.OpenPackagingConvention import OpenPackagingConvention


##  A container file that contains Cura resources that belong together.
#   Cura can install these packages to extend the program with user generated content.
#   Examples are Cura plugins or a set of material and quality profiles.
class CuraPackage(OpenPackagingConvention):

    # The following files should be ignored when adding a plugin directory.
    PLUGIN_IGNORED_FILES = [r"__pycache__", r"\.qmlc", r"\.pyc"]

    global_metadata_file = "/Metadata/package.json"
    metadata_relationship_type = "http://schemas.ultimaker.org/package/2018/relationships/curapackage_metadata"
    mime_type = "application/x-curapackage"

    # File aliases for quick and easy access.
    aliases = OrderedDict([
        (r"/materials", "/files/resources/materials"),
        (r"/qualities", "/files/resources/qualities"),
        (r"/machines", "/files/resources/machines"),
        (r"/plugins", "/files/plugins")
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
    #   \param machine_data The data of the machine definition file in bytes.
    #   \param package_filename The location to write the data to inside the package.
    def addMachine(self, machine_data: bytes, package_filename: str) -> None:
        machine_path_alias = "/machines"
        self._ensureRelationExists(virtual_path=machine_path_alias, relation_type="machine", origin="/package.json")
        self._writeToAlias(machine_path_alias, package_filename, machine_data)

    ##  Gets a list of paths to plugins in the package.
    def getPlugins(self) -> List[str]:
        return self.listPaths("/plugins")

    ##  Add a new plugin.
    #   \param plugin_root_path The folder where the plugin currently is.
    #   \param plugin_id The ID of the plugin within the package.
    def addPlugin(self, plugin_root_path: str, plugin_id: str) -> None:
        plugin_path_alias = "/plugins"
        self._ensureRelationExists(virtual_path=plugin_path_alias, relation_type="plugin", origin="/package.json")
        ignore_string = re.compile("|".join(self.PLUGIN_IGNORED_FILES))
        paths_to_add = []  # type: List[str]

        # Find which files to add.
        for root, folders, files in os.walk(plugin_root_path):
            for item_name in folders + files:
                if ignore_string.search(item_name):
                    continue
                paths_to_add.append(item_name)

        # Validate required files.
        required_paths = ["plugin.json", "__init__.py"]
        for required_path in required_paths:
            if required_path not in paths_to_add:
                raise FileNotFoundError("Required file {} not found in plugin directory {}"
                                        .format(required_path, plugin_id))

        # Add all files.
        for path in paths_to_add:
            absolute_path = os.path.join(plugin_root_path, path)
            stream = self.getStream("{}/{}/{}".format(plugin_path_alias, plugin_id, path))
            with open(absolute_path, "rb") as f:
                stream.write(f.read())

    ##  Export the package to bytes.
    def toByteArray(self, offset: int = 0, count: int = -1) -> bytes:
        self._validateMetadata()
        return super().toByteArray(offset, count)

    ##  Creates all the required content types for a .curapackage.
    def _readContentTypes(self):
        super()._readContentTypes()
        if self.mode != OpenMode.ReadOnly:
            self.addContentType(extension="xml.fdm_material", mime_type="application/x-ultimaker-material-profile")
            self.addContentType(extension="xml.fdm_material.sig", mime_type="application/x-ultimaker-material-sig")
            self.addContentType(extension="inst.cfg", mime_type="application/x-ultimaker-quality-profile")
            self.addContentType(extension="definition.json", mime_type="application/x-ultimaker-machine-profile")

    ##  Validates if the package.json metadata file contains all the required keys
    #   and if they are in the correct format.
    def _validateMetadata(self):
        # TODO
        pass
