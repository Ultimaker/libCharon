# Copyright (c) 2018 Ultimaker B.V.
# Charon is released under the terms of the LGPLv3 or higher.
import io
import os
from typing import List

import pytest

from Charon.OpenMode import OpenMode
from Charon.filetypes.CuraPackage import CuraPackage


def test_addPackageJsonMetadata():
    """
    This tests adding meta data which will eventually end up in the package.json file.
    """
    
    # Create the package.
    stream = io.BytesIO()
    package = CuraPackage()
    package.openStream(stream, mode = OpenMode.WriteOnly)
    
    # Add the metadata.
    package.setMetadata({"/package_id": "CharonTestPackage"})

    # Close the file now that we're finished writing data to it.
    package.close()

    # Open the package as read-only for testing.
    read_package = CuraPackage()
    read_package.openStream(stream, mode = OpenMode.ReadOnly)

    assert read_package.getData("/metadata/package_id").get("/metadata/package_id") == "CharonTestPackage"


@pytest.mark.parametrize("filenames", [
    ["example_material.xml.fdm_material"],  # test a single material
    ["example_material.xml.fdm_material", "example_material_two.xml.fdm_material"],  # test multiple materials
])
def test_addMaterials(filenames: List[str]):
    """
    This tests adding a material resource and relation to a .curapackage.
    """
    
    # Create the package.
    stream = io.BytesIO()
    package = CuraPackage()
    package.openStream(stream, mode = OpenMode.WriteOnly)

    # Add the material content type and relationship.
    material_path_alias = "/materials"  # This is an existing path alias in the CuraPackage file type.
    package.addRelation(virtual_path = material_path_alias, relation_type = "material", origin = "/package.json")
    package.addContentType(extension = "xml.fdm_material", mime_type = "text/xml")
    
    # Add the material files
    for filename in filenames:
        original_material = open(os.path.join(os.path.dirname(__file__), "resources", "materials", filename), "rb").read()
        packaged_material = package.getStream("{}/{}".format(material_path_alias, filename))
        packaged_material.write(original_material)
    
    # Close the file now that we're finished writing data to it.
    package.close()
    
    # Open the package as read-only for testing.
    read_package = CuraPackage()
    read_package.openStream(stream, mode = OpenMode.ReadOnly)
    available_material_resources = read_package.listPaths(material_path_alias)
    assert len(available_material_resources) == len(filenames)
    
    path_alias = read_package.aliases.get(material_path_alias)
    for filename in filenames:
        assert "{}/{}".format(path_alias, filename) in available_material_resources
