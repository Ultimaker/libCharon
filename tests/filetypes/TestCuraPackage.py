# Copyright (c) 2018 Ultimaker B.V.
# Charon is released under the terms of the LGPLv3 or higher.
import pytest
import io
import os
from typing import List

from Charon.OpenMode import OpenMode
from Charon.filetypes.CuraPackage import CuraPackage


##  Tests adding meta data which will eventually end up in the package.json file.
def test_addPackageJsonMetadata():

    # Create the package.
    stream = io.BytesIO()
    package = CuraPackage()
    package.openStream(stream, mode=OpenMode.WriteOnly)

    # Add the metadata.
    package.setMetadata({"package_id": "CharonTestPackage"})

    # Close the file now that we're finished writing data to it.
    package.close()

    # Open the package as read-only for testing.
    read_package = CuraPackage()
    read_package.openStream(stream, mode=OpenMode.ReadOnly)

    # Test two methods of retrieving the metadata.
    assert read_package.getData("/metadata/package_id").get("/metadata/package_id") == "CharonTestPackage"
    assert read_package.getMetadata("/package_id").get("/metadata/package_id") == "CharonTestPackage"

    # Test the Metadata paths.
    available_package_metadata_files = [path for path in read_package.listPaths() if "/package.json" in path]
    assert len(available_package_metadata_files) == 2  # /package_id and /package.json
    assert "/package.json" in available_package_metadata_files
    assert "/package_id" in available_package_metadata_files


# Tests adding a plugin to a .curapackage
@pytest.mark.parametrize("plugin_paths", [
    ["CuraTestPlugin"],
    ["CuraTestIgnoredFilesPlugin"],
])
def test_addPlugin(plugin_paths: List[str]):

    # Create the package.
    stream = io.BytesIO()
    package = CuraPackage()
    package.openStream(stream, mode=OpenMode.WriteOnly)

    # Add the plugins.
    for path in plugin_paths:
        package.addPlugin(open(os.path.join(os.path.dirname(__file__), "plugins", "{}.zip".format(path)), "rb").read(),
                          plugin_id=path)

    # Close the file now that we're finished writing data to it.
    package.close()

    # Open the package as read-only for testing.
    read_package = CuraPackage()
    read_package.openStream(stream, mode=OpenMode.ReadOnly)
    available_plugins = read_package.getPluginPaths()

    # Test if the required paths are there.
    path_alias = read_package._aliases.get("/plugins")
    for path in plugin_paths:
        assert "{}/{}/{}".format(path_alias, path, "plugin.json") in available_plugins
        assert "{}/{}/{}".format(path_alias, path, "__init__.py") in available_plugins


# Tests adding a broken plugin to a .curapackage
@pytest.mark.parametrize("plugin_paths", [
    ["CuraTestBrokenPlugin"]
])
def test_addBrokenPlugin(plugin_paths: List[str]):

    # Create the package.
    stream = io.BytesIO()
    package = CuraPackage()
    package.openStream(stream, mode=OpenMode.WriteOnly)

    # Add the plugins.
    with pytest.raises(FileNotFoundError):
        for path in plugin_paths:
            package.addPlugin(open(os.path.join(os.path.dirname(__file__), "plugins", "{}.zip".format(path)),
                                   "rb").read(), plugin_id=path)

    # Close the file now that we're finished writing data to it.
    package.close()

    # Open the package as read-only for testing.
    read_package = CuraPackage()
    read_package.openStream(stream, mode=OpenMode.ReadOnly)
    available_plugins = read_package.getPluginPaths()
    assert len(available_plugins) == 0  # 0 because broken plugins should not be added


# Tests adding a quality resource and relation to a .curapackage
@pytest.mark.parametrize("filenames", [
    ["example_quality.inst.cfg"],  # test a single quality
    ["example_quality.inst.cfg", "example_quality_two.inst.cfg"],  # test multiple qualities
])
def test_addQualities(filenames: List[str]):

    # Create the package.
    stream = io.BytesIO()
    package = CuraPackage()
    package.openStream(stream, mode=OpenMode.WriteOnly)

    # Add the quality files.
    for filename in filenames:
        original_quality = open(os.path.join(os.path.dirname(__file__), "resources", "qualities", filename),
                                "rb").read()
        package.addQuality(original_quality, filename)

    # Close the file now that we're finished writing data to it.
    package.close()

    # Open the package as read-only for testing.
    read_package = CuraPackage()
    read_package.openStream(stream, mode=OpenMode.ReadOnly)
    available_quality_resources = read_package.getQualityPaths()
    assert len(available_quality_resources) == len(filenames)

    # Test if the full paths are there.
    path_alias = read_package._aliases.get("/qualities")
    for filename in filenames:
        assert "{}/{}".format(path_alias, filename) in available_quality_resources


# Tests adding a material resource and relation to a .curapackage.
@pytest.mark.parametrize("filenames", [
    ["example_material.xml.fdm_material"],  # test a single material
    ["example_material.xml.fdm_material", "example_material_two.xml.fdm_material"],  # test multiple materials
])
def test_addMaterials(filenames: List[str]):

    # Create the package.
    stream = io.BytesIO()
    package = CuraPackage()
    package.openStream(stream, mode=OpenMode.WriteOnly)

    # Add the material files.
    for filename in filenames:
        original_material = open(os.path.join(os.path.dirname(__file__), "resources", "materials", filename),
                                 "rb").read()
        package.addMaterial(original_material, filename)

    # Close the file now that we're finished writing data to it.
    package.close()

    # Open the package as read-only for testing.
    read_package = CuraPackage()
    read_package.openStream(stream, mode=OpenMode.ReadOnly)
    available_material_resources = read_package.getMaterialPaths()
    assert len(available_material_resources) == len(filenames)

    # Test if the full paths are there.
    path_alias = read_package._aliases.get("/materials")
    for filename in filenames:
        assert "{}/{}".format(path_alias, filename) in available_material_resources


# Tests adding a machine resource and relation to a .curapackage.
@pytest.mark.parametrize("filenames", [
    ["example_machine.def.json"],  # test a single machine
    ["example_machine.def.json", "example_machine_two.def.json"],  # test multiple machines
])
def test_addMachines(filenames: List[str]):

    # Create the package.
    stream = io.BytesIO()
    package = CuraPackage()
    package.openStream(stream, mode=OpenMode.WriteOnly)

    # Add the material files.
    for filename in filenames:
        original_material = open(os.path.join(os.path.dirname(__file__), "resources", "definitions", filename),
                                 "rb").read()
        package.addMachine(original_material, filename)

    # Close the file now that we're finished writing data to it.
    package.close()

    # Open the package as read-only for testing.
    read_package = CuraPackage()
    read_package.openStream(stream, mode=OpenMode.ReadOnly)
    available_machine_resources = read_package.getMachinePaths()
    assert len(available_machine_resources) == len(filenames)

    # Test if the full paths are there.
    path_alias = read_package._aliases.get("/definitions")
    for filename in filenames:
        assert "{}/{}".format(path_alias, filename) in available_machine_resources


def test_getAsByteArrayAndValidate():

    # Create the package.
    stream = io.BytesIO()
    package = CuraPackage()
    package.openStream(stream, mode=OpenMode.WriteOnly)

    # Add meta data
    package.setMetadata({
        "package_id": "CharonTestPackage",
        "author/author_id": "Ultimaker"
    })

    # Close the file now that we're finished writing data to it.
    package.close()

    # Get the package as byte array which will trigger the validation of the package.json metadata file.
    read_package = CuraPackage()
    read_package.openStream(stream, mode=OpenMode.ReadOnly)
    data = read_package.toByteArray()
    with open("test.curapackage", "wb") as f:
        f.write(data)


def _test_getAsByteArrayAndValidateInvalid():

    # Create the package.
    stream = io.BytesIO()
    package = CuraPackage()
    package.openStream(stream, mode=OpenMode.WriteOnly)

    # Close the file now that we're finished writing data to it.
    # We explicitly don't add any metadata to test if a value error will be thrown.
    package.close()

    # Get the package as byte array which will trigger the validation of the package.json metadata file.
    read_package = CuraPackage()
    read_package.openStream(stream, mode=OpenMode.ReadOnly)
    with pytest.raises(ValueError):
        read_package.toByteArray()
