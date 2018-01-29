# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.

import enum #The class in this file is an enum.

##  The possible purposes for which you could open a file.
#
#   You could always open a file in read-write mode, but it's best practice to
#   open a file in specific read or write only modes if only one of the two is
#   needed. This will prevent the programmer from accidentally modifying the
#   file and may trigger some operating systems to treat the file lock
#   differently.
class OpenMode(enum.Enum):
    ##  The file can only be read from.
    ReadOnly = "r"

    ##  The file can only be written to.
    WriteOnly = "w"