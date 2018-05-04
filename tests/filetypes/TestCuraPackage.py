# Copyright (c) 2018 Ultimaker B.V.
# Charon is released under the terms of the LGPLv3 or higher.
import io
import zipfile
from xml.etree import ElementTree

from Charon.OpenMode import OpenMode
from Charon.filetypes.CuraPackage import CuraPackage


def test_addMaterial():
    """
    This tests adding a material resource and relation to a .curapackage.
    """
    
    stream = io.BytesIO()
    package = CuraPackage()
    package.openStream(stream, mode = OpenMode.WriteOnly)
    package.addContentType("xml.fdm_material", "text/xml")
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
