# Copyright (c) 2018 Ultimaker B.V.
# Charon is released under the terms of the LGPLv3 or higher.
import io
import os
from typing import List

import pytest

from Charon.OpenMode import OpenMode
from Charon.filetypes.CuraPackage import CuraPackage


##  Tests adding meta data which will eventually end up in the package.json file.
def test_addPackageJsonMetadata():

    # Create the package.
    stream = io.BytesIO()
    package = CuraPackage()
    package.openStream(stream, mode=OpenMode.WriteOnly)

    # Add the metadata.
    package.setMetadata({"/package_id": "CharonTestPackage"})

    # Close the file now that we're finished writing data to it.
    package.close()

    # Open the package as read-only for testing.
    read_package = CuraPackage()
    read_package.openStream(stream, mode=OpenMode.ReadOnly)

    # Test two methods of retrieving the metadata.
    assert read_package.getData("/metadata/package_id").get("/metadata/package_id") == "CharonTestPackage"
    assert read_package.getMetadata("/package_id").get("/metadata/package_id") == "CharonTestPackage"

    # Test the Metadata paths.
    available_package_metadata_files = read_package.listPaths("/Metadata")
    assert len(available_package_metadata_files) == 2  # /package_id and /Metadata/package.json
    assert "/Metadata/package.json" in available_package_metadata_files
    assert "/package_id" in available_package_metadata_files


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

    # Add the material files
    for filename in filenames:
        original_material = open(os.path.join(os.path.dirname(__file__), "resources", "materials", filename),
                                 "rb").read()
        package.addMaterial(original_material, filename)

    # Close the file now that we're finished writing data to it.
    package.close()

    # Open the package as read-only for testing.
    read_package = CuraPackage()
    read_package.openStream(stream, mode=OpenMode.ReadOnly)
    available_material_resources = read_package.getMaterials()
    assert len(available_material_resources) == len(filenames)

    # Test if the full paths are there.
    path_alias = read_package.aliases.get("/materials")
    for filename in filenames:
        assert "{}/{}".format(path_alias, filename) in available_material_resources
