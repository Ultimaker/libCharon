# Copyright (c) 2018 Ultimaker B.V.
# Charon is released under the terms of the LGPLv3 or higher.
import io
import os

import pytest

from Charon.OpenMode import OpenMode
from Charon.filetypes.CuraPackage import CuraPackage


@pytest.mark.parametrize("filename", ["example_material.xml.fdm_material"])
def test_addMaterial(filename: str):
    """
    This tests adding a material resource and relation to a .curapackage.
    """
    
    # Create the package.
    stream = io.BytesIO()
    package = CuraPackage()
    package.openStream(stream, mode = OpenMode.WriteOnly)

    # Add the material content type and add an example material file.
    package.addContentType(extension = "xml.fdm_material", mime_type = "text/xml")
    original_material = open(os.path.join(os.path.dirname(__file__), "resources", "materials", filename), "rb").read()
    packaged_material = package.getStream("/resources/materials/{}".format(filename))
    packaged_material.write(original_material)
    package.close()

    # Open the package as read-only for testing.
    read_package = CuraPackage()
    read_package.openStream(stream, mode = OpenMode.ReadOnly)
    available_material_resources = read_package.listPaths("/resources/materials")
    assert len(available_material_resources) == 1
    assert "/resources/materials/{}".format(filename) in available_material_resources
