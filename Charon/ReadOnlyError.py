# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.

##  Exception to indicate that an attempt was made to write to a resource that
#   is read-only.
#
#   Normally this sort of thing would be a ``PermissionError`` (the built-in
#   Python exception), but we want to be able to distinguish between these
#   errors ordinary ``PermissionErrors`` raised by the file system not having
#   access to that file.
class ReadOnlyError(PermissionError):
    ##  Creates the exception instance.
    #   \param virtual_path The resource that could not be written to. If not
    #   provided, an empty string is used which indicates that the entire file
    #   could not be written to.
    def __init__(self, virtual_path: str = "") -> None:
        self.virtual_path = virtual_path

    ##  Provides a human-readable version of this error for in the stack trace.
    def __repr__(self) -> str:
        return "ReadOnlyError({resource})".format(resource = self.virtual_path)