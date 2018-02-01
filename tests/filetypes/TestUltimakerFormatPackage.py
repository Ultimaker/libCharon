# Copyright (c) 2018 Ultimaker B.V.
# Charon is released under the terms of the LGPLv3 or higher.

import os.path #To find the resources with test packages.
import pytest #This module contains unit tests.

from Charon.filetypes.UltimakerFormatPackage import UltimakerFormatPackage #The class we're testing.
from Charon.OpenMode import OpenMode #To open archives.

##  Returns an empty package that you can try to read from.
#
#   The package has no resources at all.
@pytest.fixture()
def empty_read_ufp() -> UltimakerFormatPackage:
    result = UltimakerFormatPackage()
    result.openStream(open(os.path.join(os.path.dirname(__file__), "resources", "empty.ufp"), "rb"), "application/x-ufp", OpenMode.ReadOnly)
    return result

#### Now follow the actual tests. ####

def test_listPathsEmpty(empty_read_ufp):
    assert len(empty_read_ufp.listPaths()) == 0