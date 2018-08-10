# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.
import io
import re
from collections import OrderedDict
from typing import List, Set
from zipfile import ZipFile

from Charon.OpenMode import OpenMode
from Charon.filetypes.OpenPackagingConvention import OpenPackagingConvention


##  A container file that contains Cura resources that belong together.
#   Cura can install these packages to extend the program with user generated content.
#   Examples are Cura plugins or a set of material and quality profiles.
class CuraPackage(OpenPackagingConvention):

    # The following files should be ignored when adding a plugin directory.
    PLUGIN_IGNORED_FILES = {r"__pycache__", r"\.qmlc", r"\.pyc"}

    # The following entries in package.json are required.
    REQUIRED_METADATA_FIELDS = {
        "package_id",
        "display_name",
        "description",
        "package_type",
        "package_version",
        "sdk_version",
        "website",
        "author/author_id",
        "author/display_name",
        "author/website"
    }

    # Some file type settings.
    _global_metadata_file = "/package.json"
    _metadata_relationship_type = "http://schemas.ultimaker.org/package/2018/relationships/curapackage_metadata"
    mime_type = "application/x-curapackage"

    # File aliases for quick and easy access.
    _aliases = OrderedDict([
        (r"/materials", "/files/resources/materials"),
        (r"/qualities", "/files/resources/qualities"),
        (r"/definitions", "/files/resources/definitions"),
        (r"/plugins", "/files/plugins")
    ])

    ##  Gets a list of paths to material files in the package.
    def getMaterialPaths(self) -> List[str]:
        return [path for path in self.listPaths() if "/materials" in path]

    ##  Add a new material file.
    #   \param material_data The data of the material file in bytes.
    #   \param name The name of the file in the package.
    def addMaterial(self, material_data: bytes, name: str) -> None:
        material_path_alias = "/materials"
        self._ensureRelationExists(virtual_path=material_path_alias, relation_type="material", origin="/package.json")
        self._writeToAlias(material_path_alias, name, material_data)

    ##  Gets a list of paths to quality files in the package.
    def getQualityPaths(self) -> List[str]:
        return [path for path in self.listPaths() if "/qualities" in path]

    ##  Add a new quality file.
    #   \param: quality_data The data of the quality file in bytes.
    #   \param name The name of the file in the package.
    def addQuality(self, quality_data: bytes, name: str) -> None:
        quality_path_alias = "/qualities"
        self._ensureRelationExists(virtual_path=quality_path_alias, relation_type="quality", origin="/package.json")
        self._writeToAlias(quality_path_alias, name, quality_data)

    ##  Gets a list of paths to machine definition files in the package.
    def getMachinePaths(self) -> List[str]:
        return [path for path in self.listPaths() if "/definitions" in path]

    ##  Add a new machine definition file.
    #   \param machine_data The data of the machine definition file in bytes.
    #   \param name The name of the file in the package.
    def addMachine(self, machine_data: bytes, name: str) -> None:
        machine_path_alias = "/definitions"
        self._ensureRelationExists(virtual_path=machine_path_alias, relation_type="definition", origin="/package.json")
        self._writeToAlias(machine_path_alias, name, machine_data)

    ##  Gets a list of paths to plugins in the package.
    def getPluginPaths(self) -> List[str]:
        return [path for path in self.listPaths() if "/plugins" in path]

    ##  Add a new plugin.
    #   \param plugin_data The data in the ZIP file as bytes.
    #   \param plugin_id The ID of the plugin within the package.
    #   \raises FileNotFoundError If a required file is not in the plugin ZIP file, this error will be raised.
    def addPlugin(self, plugin_data: bytes, plugin_id: str) -> None:
        plugin_path_alias = "/plugins"
        self._ensureRelationExists(virtual_path=plugin_path_alias, relation_type="plugin", origin="/package.json")
        ignore_string = re.compile("|".join(self.PLUGIN_IGNORED_FILES))
        required_paths = ["{}/plugin.json".format(plugin_id), "{}/__init__.py".format(plugin_id)]
        paths_to_add = set()  # type: Set[str]

        # First we check if there is already a plugin with this ID in the package.
        # This is not allowed as it can result in unexpected behaviour (where only half the correct files are there).
        if "{}/{}".format(plugin_path_alias, plugin_id) in self.listPaths():
            raise FileExistsError("There is already a plugin with ID {} in the package".format(plugin_id))

        # Open the bytes as ZipFile and walk through all the files.
        with ZipFile(io.BytesIO(plugin_data), "r") as zip_file:
            # Find which files to add.
            for zip_item in zip_file.filelist:
                if ignore_string.search(zip_item.filename):
                    continue
                paths_to_add.add(zip_item.filename)
            # Validate required files.
            for required_path in required_paths:
                if required_path not in paths_to_add:
                    raise FileNotFoundError("Required file {} not found in plugin directory {}"
                                            .format(required_path, plugin_id))
            # Add all files.
            for path in paths_to_add:
                stream = self.getStream("{}/{}".format(plugin_path_alias, path))
                stream.write(zip_file.read(path))

    ##  Export the package to bytes.
    def toByteArray(self, offset: int = 0, count: int = -1) -> bytes:
        self._validateMetadata()
        return super().toByteArray(offset, count)

    ##  Creates all the required content types for a .curapackage.
    def _readContentTypes(self) -> None:
        super()._readContentTypes()
        if self._mode != OpenMode.ReadOnly:
            self.addContentType(extension="xml.fdm_material", mime_type="application/x-ultimaker-material-profile")
            self.addContentType(extension="xml.fdm_material.sig", mime_type="application/x-ultimaker-material-sig")
            self.addContentType(extension="inst.cfg", mime_type="application/x-ultimaker-quality-profile")
            self.addContentType(extension="def.json", mime_type="application/x-ultimaker-machine-definition")

    ##  Validates if the package.json metadata file contains all the required keys
    #   and if they are in the correct format.
    def _validateMetadata(self) -> None:
        for required_field in self.REQUIRED_METADATA_FIELDS:
            if not self.getMetadata("/{}".format(required_field)):
                raise ValueError("{} is a required metadata field but was not found".format(required_field))
