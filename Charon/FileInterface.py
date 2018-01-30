# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.

from io import BufferedIOBase #To indicate that getStream must return a stream.
from typing import Any, Dict, Optional

from .OpenMode import OpenMode

##  An interface for accessing files.
#
#   This interface is designed to be able to access 3D-printing related files,
#   and for container-type files to access the resources therein.
class FileInterface:
    ##  Indicate if this type of file is binary.
    #
    #   This determines if the file should be opened in binary mode or not.
    is_binary = False

    ##  Opens a file for reading or writing.
    #
    #   After opening the file, this instance will represent that file from then
    #   on, meaning that the metadata getters/setters and the streams will be
    #   functioning on that file.
    #   \param path The path to the file on local disk, relative or absolute.
    #   \param mode The mode with which to open the file (see OpenMode).
    def open(self, path: str, mode: OpenMode = OpenMode.ReadOnly):
        raise NotImplementedError("The open() function of " + self.__class__.__qualname__ + " is not implemented.")

    ##  Opens a stream for reading or writing.
    #
    #   After opening the stream, this instance will represent that stream from
    #   then on, meaning that the metadata getters/setters and the streams will
    #   be functioning on that stream.
    #   \param stream The stream to read from or write to.
    #   \param mime The MIME type of the stream. This determines what
    #   implementation is used to read/write it.
    #   \param mode The mode with which to open the file (see OpenMode).
    def openStream(self, stream: BufferedIOBase, mime: str, mode: OpenMode = OpenMode.ReadOnly):
        raise NotImplementedError("The openstream() function of " + self.__class__.__qualname__ + " is not implemented.")

    ##  Closes the opened file, releasing the resources in use for it.
    #
    #   After the file is closed, this instance can no longer be used until the
    #   ``open`` method is called again.
    def close(self):
        raise NotImplementedError("The close() function of " + self.__class__.__qualname__ + " is not implemented.")

    ##  Ensures that no buffered data is still pending to be read or written.
    def flush(self):
        raise NotImplementedError("The flush() function of " + self.__class__.__qualname__ + " is not implemented.")

    ##  Gets metadata entries in the opened file.
    #
    #   The metadata is a dictionary, where the keys are virtual paths in the
    #   subtree of the resource tree specified by ``virtual_path``. For
    #   instance, when requesting the metadata of the resource with virtual path
    #   ``/metadata``, this function could return a dictionary containing:
    #   * ``/metadata/size``: 12354
    #   * ``/metadata/toolpath/default/size``: 12000
    #   * ``/metadata/toolpath/default/machine_type``: ``ultimaker3``
    #   * ``/metadata/toolpath/default/print_time``: 121245
    #   * ``/metadata/toolpath/default/print_size``: (0, 0, 0) x (100, 100, 100)
    #
    #   But a subtree can be requested as well, such as
    #   ``/metadata/toolpath/default/size``, which would then return a
    #   dictionary containing only the key ``/metadata/toolpath/default/size``
    #   and its value, because there are no other subitems in that subtree.
    #
    #   If there is no metadata in the requested path, an empty dictionary is
    #   returned.
    #   \param virtual_path The subtree of metadata entries to get the metadata
    #   of.
    #   \return A dictionary of all the metadata entries in the selected
    #   subtree.
    def getMetadata(self, virtual_path: str) -> Dict[str, Any]:
        raise NotImplementedError("The getMetadata() function of " + self.__class__.__qualname__ + " is not implemented.")

    ##  Changes some metadata entries in the opened file.
    #
    #   The provided dictionary must have the full virtual paths of the metadata
    #   entries it wants to change as its keys, and the new values along with
    #   every key.
    #
    #   If a metadata entry didn't exist yet, it is created.
    #
    #   If a metadata entry by cannot be changed (such as the file size of a
    #   resource) then a ``ReadOnlyError`` must be raised for that resource, and
    #   none of the changes of this function call may be applied (or everything
    #   must be undone).
    #   \param metadata A dictionary of metadata entries to change.
    #   \raises ReadOnlyError A metadata entry cannot be changed (such as the
    #   file size of a resource).
    def setMetadata(self, metadata: Dict[str, Any]):
        raise NotImplementedError("The setMetadata() function of " + self.__class__.__qualname__ + " is not implemented.")

    ##  Gets an I/O stream to the resource at the specified virtual path.
    #
    #   Whether the returned stream is an input or an output stream depends on
    #   the mode that was provided in the ``open`` method. This determines
    #   whether you can read from and/or write to the stream.
    #
    #   If a resource didn't exist and you can write, the resource is created.
    #   \param virtual_path The virtual path to the resource that you want to
    #   read or write.
    #   \raises ReadOnlyError The resource doesn't exist and there are no write
    #   permissions to create it.
    def getStream(self, virtual_path) -> BufferedIOBase:
        raise NotImplementedError("The getStream() function of " + self.__class__.__qualname__ + " is not implemented.")

    ##  Gets a bytes representation of the file.
    #
    #   Resources inside the file are not supported by this method. Use
    #   ``getStream`` for that.
    #   \param offset The number of bytes to skip at the beginning of the file.
    #   \param count The maximum number of bytes to return. If the file is
    #   longer than this, it is truncated. If the file is shorter than this,
    #   fewer bytes than this might be returned. If not specified, the entire
    #   file will be returned except the initial offset.
    #   \return bytes A bytes array representing the file or a part of it.
    def toByteArray(self, offset: int = 0, count: int = -1) -> bytes:
        raise NotImplementedError("The toByteArray() function of " + self.__class__.__qualname__ + " is not implemented.")