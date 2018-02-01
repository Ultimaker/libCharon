# Copyright (c) 2018 Ultimaker B.V.
# Charon is released under the terms of the LGPLv3 or higher.

import io #To create fake streams to write to and read from.
import os.path #To find the resources with test packages.
import pytest #This module contains unit tests.

from Charon.filetypes.UltimakerFormatPackage import UltimakerFormatPackage #The class we're testing.
from Charon.OpenMode import OpenMode #To open archives.

##  Returns an empty package that you can read from.
#
#   The package has no resources at all, so reading from it will not find
#   anything.
@pytest.fixture()
def empty_read_ufp() -> UltimakerFormatPackage:
    result = UltimakerFormatPackage()
    result.openStream(open(os.path.join(os.path.dirname(__file__), "resources", "empty.ufp"), "rb"))
    yield result
    result.close()

##  Returns an empty package that you can write to.
#
#   Note that you can't really test the output of the write since you don't have
#   the stream it writes to.
@pytest.fixture()
def empty_write_ufp() -> UltimakerFormatPackage:
    result = UltimakerFormatPackage()
    result.openStream(io.BytesIO(), "application/x-ufp", OpenMode.WriteOnly)
    yield result
    result.close()

#### Now follow the actual tests. ####

##  Tests whether an empty file is recognised as empty.
def test_listPathsEmpty(empty_read_ufp: UltimakerFormatPackage):
    assert len(empty_read_ufp.listPaths()) == 0

##  Tests getting write streams of various resources that may or may not exist.
#
#   Every test will write some arbitrary data to it to see that that also works.
@pytest.mark.parametrize("virtual_path", ["/dir/file", "/file", "dir/file", "file", "/Metadata", "/_rels/.rels"])
def test_getWriteStream(empty_write_ufp: UltimakerFormatPackage, virtual_path: str):
    stream = empty_write_ufp.getStream(virtual_path)
    stream.write(b"The test is successful.")