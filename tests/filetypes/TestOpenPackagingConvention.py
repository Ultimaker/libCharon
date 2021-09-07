# Copyright (c) 2018 Ultimaker B.V.
# Charon is released under the terms of the LGPLv3 or higher.
import io #To create fake streams to write to and read from.
import os #To find the resources with test packages.
import pytest #This module contains unit tests.
import zipfile #To inspect the contents of the zip archives.
import xml.etree.ElementTree as ET #To inspect the contents of the OPC-spec files in the archives.
from collections import OrderedDict
from typing import List, Generator

from Charon.filetypes.OpenPackagingConvention import OpenPackagingConvention, OPCError  # The class we're testing.
from Charon.OpenMode import OpenMode #To open archives.

##  Returns an empty package that you can read from.
#
#   The package has no resources at all, so reading from it will not find
#   anything.
@pytest.fixture()
def empty_read_opc() -> Generator[OpenPackagingConvention, None, None]:
    result = OpenPackagingConvention()
    result.openStream(open(os.path.join(os.path.dirname(__file__), "resources", "empty.opc"), "rb"))
    yield result
    result.close()


##  Returns a package that has a single file in it.
#
#   The file is called "hello.txt" and contains the text "Hello world!" encoded
#   in UTF-8.
@pytest.fixture()
def single_resource_read_opc() -> Generator[OpenPackagingConvention, None, None]:
    result = OpenPackagingConvention()
    result.openStream(open(os.path.join(os.path.dirname(__file__), "resources", "hello.opc"), "rb"))
    yield result
    result.close()


##  Returns an empty package that you can write to.
#
#   Note that you can't really test the output of the write since you don't have
#   the stream it writes to.
@pytest.fixture()
def empty_write_opc() -> Generator[OpenPackagingConvention, None, None]:
    result = OpenPackagingConvention()
    result.openStream(io.BytesIO(), "application/x-opc", OpenMode.WriteOnly)
    yield result
    result.close()


#### Now follow the actual tests. ####

##  Tests whether an empty file is recognised as empty.
def test_listPathsEmpty(empty_read_opc: OpenPackagingConvention):
    assert len(empty_read_opc.listPaths()) == 0


##  Tests getting write streams of various resources that may or may not exist.
#
#   Every test will write some arbitrary data to it to see that that also works.
@pytest.mark.parametrize("virtual_path", ["/dir/file", "/file", "dir/file", "file", "/Metadata"]) #Some extra tests without initial slash to test robustness.
def test_getWriteStream(empty_write_opc: OpenPackagingConvention, virtual_path: str):
    stream = empty_write_opc.getStream(virtual_path)
    stream.write(b"The test is successful.")


##  Tests not allowing to open relationship file directly to prevent mistakes.
@pytest.mark.parametrize("virtual_path", ["/_rels/.rels"])
def test_getWriteStream_forbidOnRels(empty_write_opc: OpenPackagingConvention, virtual_path: str):
    with pytest.raises(OPCError):
        empty_write_opc.getStream(virtual_path)


##  Tests writing data to an archive, then reading it back.
@pytest.mark.parametrize("virtual_path", ["/dir/file", "/file", "/Metadata"]) #Don't try to read .rels back. That won't work.
def test_cycleSetDataGetData(virtual_path: str):
    test_data = b"Let's see if we can read this data back."

    stream = io.BytesIO()
    package = OpenPackagingConvention()
    package.openStream(stream, mode = OpenMode.WriteOnly)
    package.setData({virtual_path: test_data})
    package.close()

    stream.seek(0)
    package = OpenPackagingConvention()
    package.openStream(stream)
    result = package.getData(virtual_path)

    assert len(result) == 1 #This data must be the only data we've found.
    assert virtual_path in result #The path must be in the dictionary.
    assert result[virtual_path] == test_data #The data itself is still correct.


@pytest.mark.parametrize("virtual_path, path_list", [
    ("/foo/materials", ["/foo/materials", "/[Content_Types].xml", "/_rels/.rels"]),
    ("/materials", ["/files/materials", "/[Content_Types].xml", "/_rels/.rels"])
])
def test_aliases_replacement(virtual_path: str, path_list: List[str]):
    test_data = b"Let's see if we can read this data back."

    stream = io.BytesIO()
    package = OpenPackagingConvention()
    package._aliases = OrderedDict([
        (r"/materials", "/files/materials")
    ])
    package.openStream(stream, mode = OpenMode.WriteOnly)
    package.setData({virtual_path: test_data})
    package.close()

    stream.seek(0)
    package = OpenPackagingConvention()
    package.openStream(stream)
    result = package.listPaths()

    assert result == path_list

##  Tests writing data via a stream to an archive, then reading it back via a
#   stream.
@pytest.mark.parametrize("virtual_path", ["/dir/file", "/file", "/Metadata"])
def test_cycleStreamWriteRead(virtual_path: str):
    test_data = b"Softly does the river flow, flow, flow."

    stream = io.BytesIO()
    package = OpenPackagingConvention()
    package.openStream(stream, mode = OpenMode.WriteOnly)
    resource = package.getStream(virtual_path)
    resource.write(test_data)
    package.close()

    stream.seek(0)
    package = OpenPackagingConvention()
    package.openStream(stream)
    resource = package.getStream(virtual_path)
    result = resource.read()

    assert result == test_data


##  Tests setting metadata in an archive, then reading that metadata back.
@pytest.mark.parametrize("virtual_path", ["/Metadata/some/global/setting", "/hello.txt/test", "/also/global/entry"])
def test_cycleSetMetadataGetMetadata(virtual_path: str):
    test_data = "Hasta la vista, baby."

    stream = io.BytesIO()
    package = OpenPackagingConvention()
    package.openStream(stream, mode = OpenMode.WriteOnly)
    package.setData({"/hello.txt": b"Hello world!"}) #Add a file to attach non-global metadata to.
    package.setMetadata({virtual_path: test_data})
    package.close()

    stream.seek(0)
    package = OpenPackagingConvention()
    package.openStream(stream)
    result = package.getMetadata(virtual_path)
    
    prefixed_virtual_path = "/metadata{}".format(virtual_path)

    assert len(result) == 1 #Only one metadata entry was set.
    assert prefixed_virtual_path in result #And it was the correct entry.
    assert result[prefixed_virtual_path] == test_data #With the correct value.


##  Tests toByteArray with its parameters.
#
#   This doesn't test if the bytes are correct, because that is the task of the
#   zipfile module. We merely test that it gets some bytes array and that the
#   offset and size parameters work.
def test_toByteArray(single_resource_read_opc):
    original = single_resource_read_opc.toByteArray()
    original_length = len(original)

    #Even empty zip archives are already 22 bytes, so offsets and sizes of less than that should be okay.
    result = single_resource_read_opc.toByteArray(offset = 10)
    assert len(result) == original_length - 10 #The first 10 bytes have fallen off.

    result = single_resource_read_opc.toByteArray(count = 8)
    assert len(result) == 8 #Limited to size 8.

    result = single_resource_read_opc.toByteArray(offset = 10, count = 8)
    assert len(result) == 8 #Still limited by the size, even though there is an offset.

    result = single_resource_read_opc.toByteArray(count = 999999) #This is a small file, definitely smaller than 1MiB.
    assert len(result) == original_length #Should be limited to the actual file length.


##  Tests toByteArray when loading from a stream.
def test_toByteArrayStream():
    stream = io.BytesIO()
    package = OpenPackagingConvention()
    package.openStream(stream, mode = OpenMode.WriteOnly)
    package.setData({"/hello.txt": b"Hello world!"}) #Add some arbitrary data so that the file size is not trivial regardless of what format is used.
    package.close()

    stream.seek(0)
    package = OpenPackagingConvention()
    package.openStream(stream)
    result = package.toByteArray()

    assert len(result) > 0 #There must be some data in it.


##  Tests whether a content type gets added and that it gets added in the
#   correct location.
def test_addContentType():
    stream = io.BytesIO()
    package = OpenPackagingConvention()
    package.openStream(stream, mode = OpenMode.WriteOnly)
    package.addContentType("lol", "audio/x-laughing")
    package.close()

    stream.seek(0)
    #This time, open as .zip to just inspect the file contents.
    archive = zipfile.ZipFile(stream)
    assert "/[Content_Types].xml" in archive.namelist()
    content_types = archive.open("/[Content_Types].xml").read()
    content_types_element = ET.fromstring(content_types)

    defaults = content_types_element.findall("{http://schemas.openxmlformats.org/package/2006/content-types}Default")
    assert len(defaults) == 2 #We only added one content type, but there must also be the .rels content type.
    for default in defaults:
        assert "Extension" in default.attrib
        assert "ContentType" in default.attrib
        assert default.attrib["Extension"] in ["lol", "rels"]
        if default.attrib["Extension"] == "lol":
            assert default.attrib["ContentType"] == "audio/x-laughing"
        elif default.attrib["Extension"] == "rels":
            assert default.attrib["ContentType"] == "application/vnd.openxmlformats-package.relationships+xml"


##  Tests whether a relation gets added and that it gets saved in the correct
#   location.
def test_addRelation():
    stream = io.BytesIO()
    package = OpenPackagingConvention()
    package.openStream(stream, mode = OpenMode.WriteOnly)
    package.setData({"/whoo.txt": b"Boo", "/whoo.enhanced.txt": b"BOOOO!", "/whoo.enforced.txt": b"BOOOOOOOOOO!"}) #Need 3 files: One base and two that are related.
    package.addRelation("whoo.enhanced.txt", "An enhanced version of it.", "whoo.txt")
    package.addRelation("whoo.enforced.txt", "A greatly enhanced version of it.", "whoo.txt")
    package.close()

    stream.seek(0)
    #This time, open as .zip to just inspect the file contents.
    archive = zipfile.ZipFile(stream)
    assert "/_rels/whoo.txt.rels" in archive.namelist() #It must create a file specifically for whoo.txt
    relations = archive.open("/_rels/whoo.txt.rels").read()
    relations_element = ET.fromstring(relations)

    both_relations = relations_element.findall("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship")
    assert len(both_relations) == 2 #We added two relations.
    for relation in both_relations:
        assert "Id" in relation.attrib
        assert "Target" in relation.attrib
        assert "Type" in relation.attrib
        assert relation.attrib["Target"] == "/whoo.enhanced.txt" or relation.attrib["Target"] == "/whoo.enforced.txt"
        if relation.attrib["Target"] == "/whoo.enhanced.txt":
            assert relation.attrib["Type"] == "An enhanced version of it."
        elif relation.attrib["Target"] == "/whoo.enforced.txt":
            assert relation.attrib["Type"] == "A greatly enhanced version of it."
    assert both_relations[0].attrib["Id"] != both_relations[1].attrib["Id"] #Id must be unique.


##  Tests getting the size of a file.
#
#   This is implemented knowing the contents of single_resource_read_opc.
def test_getMetadataSize(single_resource_read_opc):
    metadata = single_resource_read_opc.getMetadata("/hello.txt/size")
    assert "/metadata/hello.txt/size" in metadata
    assert metadata["/metadata/hello.txt/size"] == len("Hello world!\n".encode("UTF-8")) #Compare with the length of the file's contents as encoded in UTF-8.
