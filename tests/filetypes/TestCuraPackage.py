# Copyright (c) 2018 Ultimaker B.V.
# Charon is released under the terms of the LGPLv3 or higher.
import io
import os
import zipfile
from xml.etree import ElementTree

import pytest

from Charon.OpenMode import OpenMode
from Charon.filetypes.CuraPackage import CuraPackage


@pytest.mark.parametrize("filename", ["resources/materials/example_material.xml.fdm_material"])
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
    original_material = open(os.path.join(os.path.dirname(__file__), filename), "rb").read()
    packaged_material = package.getStream("/{}".format(filename))
    packaged_material.write(original_material)
    package.close()

    # Open the file as ZIP and assert the contents are correct.
    archive = zipfile.ZipFile(stream)
    
    assert "/[Content_Types].xml" in archive.namelist()
    
    content_types = archive.open("/[Content_Types].xml").read()
    content_types_element = ElementTree.fromstring(content_types)
    defaults = content_types_element.findall("{http://schemas.openxmlformats.org/package/2006/content-types}Default")

    assert len(defaults) == 2  # Assert the .rels content type and the custom content type exist.

    for default in defaults:
        assert default.attrib["Extension"] in ["xml.fdm_material", "rels"]
        if default.attrib["Extension"] == "lol":
            assert default.attrib["ContentType"] == "text/xml"

    package_files = archive.namelist()
    
    assert "/{}".format(filename) in package_files
