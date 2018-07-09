# Copyright (c) 2018 Ultimaker B.V.
# Charon is released under the terms of the LGPLv3 or higher.
import os

from Charon.VirtualFile import VirtualFile


def test_GCodeReader():
    f = VirtualFile()
    f.open(os.path.join(os.path.dirname(__file__), "resources", "um3.gcode"))
    assert f.getData("/metadata")["/metadata/toolpath/default/flavor"] == "Griffin"
    assert b"M104" in f.getStream("/toolpath").read()
    f.close()


def test_GCodeGzReader():
    f = VirtualFile()
    f.open(os.path.join(os.path.dirname(__file__), "resources", "um3.gcode.gz"))
    assert f.getData("/metadata")["/metadata/toolpath/default/flavor"] == "Griffin"
    assert b"M104" in f.getStream("/toolpath").read()
    f.close()
