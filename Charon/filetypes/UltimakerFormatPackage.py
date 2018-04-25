# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.

from collections import OrderedDict  # To specify the aliases in order.
from io import BufferedIOBase, BytesIO, TextIOWrapper  # For the type of input of openStream and to create binary output streams for getting metadata.
import json  # The metadata format.
import re  # To find the path aliases.
from typing import Any, Dict, List
import xml.etree.ElementTree as ET  # For writing XML manifest files.
import zipfile

from ..FileInterface import FileInterface  # The interface we're implementing.
from ..OpenMode import OpenMode  # To detect whether we want to read and/or write to the file.
from ..ReadOnlyError import ReadOnlyError  # To be thrown when trying to write while in read-only mode.
from ..WriteOnlyError import WriteOnlyError  # To be thrown when trying to read while in write-only mode.

from .GCodeFile import GCodeFile  # Required for fallback G-Code header parsing.


##  A container file type that contains multiple 3D-printing related files that
#   belong together.
class UltimakerFormatPackage(FileInterface):
    # Some constants related to this format.
    xml_header = ET.ProcessingInstruction("xml", "version=\"1.0\" encoding=\"UTF-8\"")  # Header element being put atop every XML file.
    content_types_file = "/[Content_Types].xml"  # Where the content types file is.
    global_metadata_file = "/Metadata/UFP_Global.json"  # Where the global metadata file is.
    ufp_metadata_relationship_type = "http://schemas.ultimaker.org/package/2018/relationships/ufp_metadata"  # Unique identifier of the relationship type that relates UFP metadata to files.
    metadata_prefix = "/metadata"
    aliases = OrderedDict([  # Virtual path aliases. Keys are regex. Order matters!
        (r"^/preview/default", "/Metadata/thumbnail.png"),
        (r"^/preview", "/Metadata/thumbnail.png"),
        (r"^/toolpath/default", "/3D/model.gcode"),
        (r"^/toolpath", "/3D/model.gcode"),
    ])

    mime_type = "application/x-ufp"

    is_binary = True  # This file needs to be opened in binary mode.

    ##  Initialises the fields of this class.
    def __init__(self):
        self.mode = None  # Whether we're in read or write mode.
        self.stream = None  # The currently open stream.
        self.zipfile = None  # The zip interface to the currently open stream.
        self.metadata = {}  # The metadata in the currently open file.
        self.content_types_element = None  # An XML element holding all the content types.
        self.relations = {}  # For each virtual path, a relations XML element (which is left out of the file if empty).
        self._open_bytes_streams = {}  # With old Python versions, the currently open BytesIO streams that need to be flushed, by their virtual path.

        # The zipfile module may only have one write stream open at a time. So when you open a new stream, close the previous one.
        self._last_open_path = None
        self._last_open_stream = None

    def openStream(self, stream: BufferedIOBase, mime: str = "application/x-ufp", mode: OpenMode = OpenMode.ReadOnly) -> None:
        self.mode = mode
        self.stream = stream #A copy in case we need to rewind for toByteArray. We should mostly be reading via self.zipfile.
        self.zipfile = zipfile.ZipFile(self.stream, self.mode.value, compression = zipfile.ZIP_DEFLATED)

        self._readContentTypes()  # Load or create the content types element.
        self._readRels()  # Load or create the relations.
        self._readMetadata()  # Load the metadata, if any.

    def close(self) -> None:
        if not self.stream:
            raise ValueError("This file is already closed.")
        self.flush()
        self.zipfile.close()

    def flush(self) -> None:
        if not self.stream:
            raise ValueError("Can't flush a closed file.")
        if self.mode == OpenMode.ReadOnly:
            return  # No need to flush reading of zip archives as they are blocking calls.

        if self._last_open_stream is not None and self._last_open_path not in self._open_bytes_streams:
            self._last_open_stream.close()

        # If using old Python versions (<= 3.5), the write streams were kept in memory to be written all at once when flushing.
        for virtual_path, stream in self._open_bytes_streams.items():
            stream.seek(0)
            self.zipfile.writestr(virtual_path, stream.read())
            stream.close()

        self._writeMetadata()  # Metadata must be updated first, because that adds rels and a content type.
        self._writeContentTypes()
        self._writeRels()

    def listPaths(self) -> List[str]:
        if not self.stream:
            raise ValueError("Can't list the paths in a closed file.")
        return list(self.metadata.keys()) + [self._zipNameToVirtualPath(zip_name) for zip_name in self.zipfile.namelist()]

    def getData(self, virtual_path) -> Dict[str, Any]:
        if not self.stream:
            raise ValueError("Can't get data from a closed file.")
        if self.mode == OpenMode.WriteOnly:
            raise WriteOnlyError(virtual_path)

        result = {}
        if virtual_path.startswith(self.metadata_prefix):
            result = self.getMetadata(virtual_path[len(self.metadata_prefix):])
        else:
            canonical_path = self._processAliases(virtual_path)
            if self._resource_exists(canonical_path):
                result[virtual_path] = self.getStream(canonical_path).read()  # In case of a name clash, the file wins. But that shouldn't be possible.

        return result

    def setData(self, data: Dict[str, Any]) -> None:
        if not self.stream:
            raise ValueError("Can't change the data in a closed file.")
        if self.mode == OpenMode.ReadOnly:
            raise ReadOnlyError()
        for virtual_path, value in data.items():
            if virtual_path.startswith(self.metadata_prefix):  # Detect metadata by virtue of being in the Metadata folder.
                self.setMetadata({virtual_path: value[len(self.metadata_prefix):]})
            else:  # Virtual file resources.
                self.getStream(virtual_path).write(value)

    def getMetadata(self, virtual_path: str) -> Dict[str, Any]:
        if not self.stream:
            raise ValueError("Can't get metadata from a closed file.")
        if self.mode == OpenMode.WriteOnly:
            raise WriteOnlyError(virtual_path)
        canonical_path = self._processAliases(virtual_path)

        # Find all metadata that begins with the specified virtual path!
        result = {}

        if canonical_path in self.metadata:  # The exact match.
            result[self.metadata_prefix + virtual_path] = self.metadata[canonical_path]
        for entry_path, value in self.metadata.items():
            # We only want to match subdirectories of the provided virtual paths.
            # So if you provide "/foo" then we don't want to match on "/foobar"
            # but we do want to match on "/foo/zoo". This is why we check if they
            # start with the provided virtual path plus a slash.
            if entry_path.startswith(canonical_path + "/"):
                # We need to return the originally requested alias, so replace the canonical path with the virtual path.
                result[self.metadata_prefix + virtual_path + "/" + entry_path[len(canonical_path) + 1:]] = value

        # If requesting the size of a file.
        if canonical_path.endswith("/size"):
            requested_resource = canonical_path[:-len("/size")]
            if self._resource_exists(requested_resource):
                result[self.metadata_prefix + virtual_path] = self.zipfile.getinfo(requested_resource.strip("/")).file_size

        return result

    def setMetadata(self, metadata: Dict[str, Any]) -> None:
        if not self.stream:
            raise ValueError("Can't change metadata in a closed file.")
        if self.mode == OpenMode.ReadOnly:
            raise ReadOnlyError()
        metadata = {self._processAliases(virtual_path): metadata[virtual_path] for virtual_path in metadata}
        self.metadata.update(metadata)

    def getStream(self, virtual_path: str) -> BufferedIOBase:
        if not self.stream:
            raise ValueError("Can't get a stream from a closed file.")

        if virtual_path.startswith(self.metadata_prefix):
            return BytesIO(json.dumps(self.getMetadata(virtual_path[len(self.metadata_prefix):])).encode("UTF-8"))

        virtual_path = self._processAliases(virtual_path)
        if self._resource_exists(virtual_path) or self.mode == OpenMode.WriteOnly: # In write-only mode, create a new file instead of reading metadata.
            # The zipfile module may only have one write stream open at a time. So when you open a new stream, close the previous one.
            if self._last_open_stream is not None and self._last_open_path not in self._open_bytes_streams: # Don't close streams that we still need to flush.
                self._last_open_stream.close()

            # If we are requesting a stream of an image resized, resize the image and return that.
            if self.mode == OpenMode.ReadOnly and ".png/" in virtual_path:
                png_file = virtual_path[:virtual_path.find(".png/") + 4]
                size_spec = virtual_path[virtual_path.find(".png/") + 5:]
                if re.match(r"^\s*\d+\s*x\s*\d+\s*$", size_spec):
                    dimensions = []
                    for dimension in re.finditer(r"\d+", size_spec):
                        dimensions.append(int(dimension.group()))
                    return self._resizeImage(png_file, dimensions[0], dimensions[1])

            self._last_open_path = virtual_path
            try: # If it happens to match some existing PNG file, we have to rescale that file and return the result.
                self._last_open_stream = self.zipfile.open(virtual_path, self.mode.value)
            except RuntimeError:  # Python 3.5 and before couldn't open resources in the archive in write mode.
                self._last_open_stream = BytesIO()
                self._open_bytes_streams[virtual_path] = self._last_open_stream  # Save this for flushing later.
            return self._last_open_stream

    def toByteArray(self, offset: int = 0, count: int = -1) -> bytes:
        if not self.stream:
            raise ValueError("Can't get the bytes from a closed file.")
        if self.mode == OpenMode.WriteOnly:
            raise WriteOnlyError()

        self.zipfile.close()  # Close the zipfile first so that we won't be messing with the stream without its consent.

        self.stream.seek(offset)
        result = self.stream.read(count)

        self.zipfile = zipfile.ZipFile(self.stream, self.mode.value, compression = zipfile.ZIP_DEFLATED)
        return result

    ##  Adds a new content type to the archive.
    #   \param extension The file extension of the type
    def addContentType(self, extension: str, mime_type: str) -> None:
        if not self.stream:
            raise ValueError("Can't add a content type to a closed file.")
        if self.mode == OpenMode.ReadOnly:
            raise ReadOnlyError()

        # First check if it already exists.
        for content_type in self.content_types_element.iterfind("Default"):
            if "Extension" in content_type.attrib and content_type.attrib["Extension"] == extension:
                raise UFPError("Content type for extension {extension} already exists.".format(extension = extension))

        ET.SubElement(self.content_types_element, "Default", Extension = extension, ContentType = mime_type)

    ##  Adds a relation concerning a file type.
    #   \param virtual_path The target file that the relation is about.
    #   \param relation_type The type of the relation. Any reader of UFP should
    #   be able to understand all types that are added via relations.
    #   \param origin The origin of the relation. If the relation concerns a
    #   specific directory or specific file, then you should point to the
    #   virtual path of that file here.
    def addRelation(self, virtual_path: str, relation_type: str, origin: str = "") -> None:
        if not self.stream:
            raise ValueError("Can't add a relation to a closed file.")
        if self.mode == OpenMode.ReadOnly:
            raise ReadOnlyError(virtual_path)
        virtual_path = self._processAliases(virtual_path)

        # First check if it already exists.
        if origin not in self.relations:
            self.relations[origin] = ET.Element("Relationships", xmlns = "http://schemas.openxmlformats.org/package/2006/relationships")
        else:
            for relationship in self.relations[origin].iterfind("Relationship"):
                if "Target" in relationship.attrib and relationship.attrib["Target"] == virtual_path:
                    raise UFPError("Relation for virtual path {target} already exists.".format(target = virtual_path))

        # Find a unique name.
        unique_id = 0
        while True:
            for relationship in self.relations[origin].iterfind("Relationship"):
                if "Id" in relationship.attrib and relationship.attrib["Id"] == "rel" + str(unique_id):
                    break
            else:  # Unique ID didn't exist yet! It's safe to use
                break
            unique_id += 1
        unique_name = "rel" + str(unique_id)

        # Create the element itself.
        ET.SubElement(self.relations[origin], "Relationship", Target = virtual_path, Type = relation_type, Id = unique_name)

    ##  Figures out if a resource exists in the archive.
    #
    #   This will not match on metadata, only on normal resources.
    #   \param virtual_path: The path to test for.
    #   \return ``True`` if it exists as a normal resource, or ``False`` if it
    #   doesn't.
    def _resource_exists(self, virtual_path: str) -> bool:
        for zip_name in self.zipfile.namelist():
            zip_virtual_path = self._zipNameToVirtualPath(zip_name)
            if virtual_path == zip_virtual_path:
                return True
            if zip_virtual_path.endswith(".png") and virtual_path.startswith(zip_virtual_path + "/"):  # We can rescale PNG images if you want.
                if re.match(r"^\s*\d+\s*x\s*\d+\s*$", virtual_path[len(zip_virtual_path) + 1:]):  # Matches the form "NxM" with optional whitespace.
                    return True
        return False

    ##  Dereference the aliases for UFP files.
    #
    #   This also adds a slash in front of every virtual path if it has no slash
    #   yet, to allow referencing virtual paths with or without the initial
    #   slash.
    def _processAliases(self, virtual_path: str) -> str:
        if not virtual_path.startswith("/"):
            virtual_path = "/" + virtual_path

        # Replace all aliases.
        for regex, replacement in self.aliases.items():
            virtual_path = re.sub(regex, replacement, virtual_path)

        return virtual_path

    ##  Convert the resource name inside the zip to a virtual path as this
    #   library specifies it should be.
    #   \param zip_name The name in the zip file according to zipfile module.
    #   \return The virtual path of that resource.
    def _zipNameToVirtualPath(self, zip_name: str) -> str:
        if not zip_name.startswith("/"):
            return "/" + zip_name
        return zip_name

    ##  Resize an image to the specified dimensions.
    #
    #   For now you may assume that the input image is PNG formatted.
    #   \param virtual_path The virtual path pointing to an image in the
    #   zipfile.
    #   \param width The desired width of the image.
    #   \param height The desired height of the image.
    #   \return A bytes stream representing a new PNG image with the desired
    #   width and height.
    def _resizeImage(self, virtual_path: str, width: int, height: int) -> BufferedIOBase:
        input = self.getStream(virtual_path)
        try:
            from PyQt5.QtGui import QImage
            from PyQt5.QtCore import Qt, QBuffer

            image = QImage()
            image.loadFromData(input.read())
            image = image.scaled(width, height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            output_buffer = QBuffer()
            output_buffer.open(QBuffer.ReadWrite)
            image.save(output_buffer, "PNG")
            output_buffer.seek(0)  # Reset that buffer so that the next guy can request it.
            return BytesIO(output_buffer.readAll())
        except ImportError:
            # TODO: Try other image loaders.
            raise  # Raise import error again if we find no other image loaders.

    #### Below follow some methods to read/write components of the archive. ####

    ##  When loading a file, load the relations from the archive.
    #
    #   If the relations are missing, empty elements are created.
    def _readRels(self) -> None:
        self.relations[""] = ET.Element("Relationships", xmlns = "http://schemas.openxmlformats.org/package/2006/relationships") #There must always be a global relationships document.

        # Below is some parsing of paths and extensions.
        # Normally you'd use os.path for this. But this is platform-dependent.
        # For instance, the path separator in Windows is a backslash, but zipfile still uses a slash on Windows.
        # So instead we have custom implementations here. Sorry.

        for virtual_path in self.zipfile.namelist():
            virtual_path = self._zipNameToVirtualPath(virtual_path)
            if not virtual_path.endswith(".rels"):  # We only want to read rels files.
                continue
            directory = virtual_path[:virtual_path.rfind("/")]  # Before the last slash.
            if directory != "_rels" and not directory.endswith("/_rels"):  # Rels files must be in a directory _rels.
                continue

            document = ET.fromstring(self.zipfile.open(virtual_path).read())

            # Find out what file or directory this relation is about.
            origin_filename = virtual_path[virtual_path.rfind("/") + 1:-len(".rels")] #Just the filename (no path) and without .rels extension.
            origin_directory = directory[:-len("/_rels")] #The parent path. We already know it's in the _rels directory.
            origin = (origin_directory + "/" if (origin_directory != "") else "") + origin_filename

            self.relations[origin] = document

    ##  At the end of writing a file, write the relations to the archive.
    #
    #   This should be written at the end of writing an archive, when all
    #   relations are known.
    def _writeRels(self) -> None:
        # Below is some parsing of paths and extensions.
        # Normally you'd use os.path for this. But this is platform-dependent.
        # For instance, the path separator in Windows is a backslash, but zipfile still uses a slash on Windows.
        # So instead we have custom implementations here. Sorry.

        for origin, element in self.relations.items():
            # Find out where to store the rels file.
            if "/" not in origin:  # Is in root.
                origin_directory = ""
                origin_filename = origin
            else:
                origin_directory = origin[:origin.rfind("/")]
                origin_filename = origin[origin.rfind("/") + 1:]
            relations_file = origin_directory + "/_rels/" + origin_filename + ".rels"

            self._indent(element)
            self.zipfile.writestr(relations_file, ET.tostring(self.xml_header) + b"\n" + ET.tostring(element))

    ##  When loading a file, load the content types from the archive.
    #
    #   If the content types are missing, an empty element is created.
    def _readContentTypes(self) -> None:
        if self.content_types_file in self.zipfile.namelist():
            content_types_element = ET.fromstring(self.zipfile.open(self.content_types_file).read())
            if content_types_element:
                self.content_types_element = content_types_element
        if not self.content_types_element:
            self.content_types_element = ET.Element("Types", xmlns = "http://schemas.openxmlformats.org/package/2006/content-types")
        # If there is no type for the .rels file, create it.
        if self.mode != OpenMode.ReadOnly:
            for type_element in self.content_types_element.iterfind("{http://schemas.openxmlformats.org/package/2006/content-types}Default"):
                if "Extension" in type_element.attrib and type_element.attrib["Extension"] == "rels":
                    break
            else:
                ET.SubElement(self.content_types_element, "Default", Extension = "rels", ContentType = "application/vnd.openxmlformats-package.relationships+xml")

    ##  At the end of writing a file, write the content types to the archive.
    #
    #   This should be written at the end of writing an archive, when all
    #   content types are known.
    def _writeContentTypes(self) -> None:
        self._indent(self.content_types_element)
        self.zipfile.writestr(self.content_types_file, ET.tostring(self.xml_header) + b"\n" + ET.tostring(self.content_types_element))

    ##  When loading a file, read its metadata from the archive.
    #
    #   This depends on the relations! Read the relations first!
    def _readMetadata(self) -> None:
        for origin, relations_element in self.relations.items():
            for relationship in relations_element.iterfind("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
                if "Target" not in relationship.attrib or "Type" not in relationship.attrib: #These two are required, and we actually need them here. Better ignore this one.
                    continue
                if relationship.attrib["Type"] != self.ufp_metadata_relationship_type: #Not interested in this one. It's not metadata that we recognise.
                    continue
                metadata_file = relationship.attrib["Target"]
                if metadata_file not in self.zipfile.namelist(): #The metadata file is unknown to us.
                    continue

                metadata = json.load(self.zipfile.open(metadata_file))
                if metadata_file == self.global_metadata_file: #Store globals as if coming from root.
                    metadata_file = ""
                elif metadata_file.endswith(".json"): #Metadata files should be named <filename.ext>.json, meaning that they are metadata about <filename.ext>.
                    metadata_file = metadata_file[:-len(".json")]
                self._readMetadataElement(metadata, metadata_file)

        if self.mode != OpenMode.WriteOnly and not self.getMetadata("/3D/model.gcode"):
            gcode_stream = TextIOWrapper(self.zipfile.open("/3D/model.gcode"))
            header_data = GCodeFile.parseHeader(gcode_stream, prefix = "/3D/model.gcode/")
            self.metadata.update(header_data)

    ##  Reads a single node of metadata from a JSON document (recursively).
    #   \param element The node in the JSON document to read.
    #   \param current_path The path towards the current document.
    def _readMetadataElement(self, element: Dict[str, Any], current_path: str) -> None:
        for key, value in element.items():
            if isinstance(value, dict):  # json structures stuff in dicts if it is a subtree.
                self._readMetadataElement(value, current_path + "/" + key)
            else:
                self.metadata[current_path + "/" + key] = value

    ##  At the end of writing a file, write the metadata to the archive.
    #
    #   This should be written at the end of writing an archive, when all
    #   metadata is known.
    #
    #   ALWAYS WRITE METADATA BEFORE UPDATING RELS AND CONTENT TYPES.
    def _writeMetadata(self) -> None:
        keys_left = set(self.metadata.keys()) #The keys that are not associated with a particular file (global metadata).
        metadata_per_file = {}
        for file_name in self.zipfile.namelist():
            metadata_per_file[file_name] = {}
            for metadata_key in self.metadata:
                if metadata_key.startswith(file_name + "/"):
                    # Strip the prefix: "/a/b/c.stl/print_time" becomes just "print_time" about the file "/a/b/c.stl".
                    metadata_per_file[file_name][metadata_key[len(file_name) + 1:]] = self.metadata[metadata_key]
                    keys_left.remove(metadata_key)
        # keys_left now contains only global metadata keys.

        global_metadata = {key:self.metadata[key] for key in keys_left}
        if len(global_metadata) > 0:
            self._writeMetadataToFile(global_metadata, self.global_metadata_file)
            self.addRelation(self.global_metadata_file, self.ufp_metadata_relationship_type)
        for file_name, metadata in metadata_per_file.items():
            if len(metadata) > 0:
                self._writeMetadataToFile(metadata, file_name + ".json")
                self.addRelation(file_name + ".json", self.ufp_metadata_relationship_type)
        if len(self.metadata) > 0:  # If we've written any metadata at all, we must include the content type as well.
            try:
                self.addContentType(extension = "json", mime_type = "text/json")
            except UFPError:  # User may already have defined this content type himself.
                pass

    ##  Writes one dictionary of metadata to a JSON file.
    #   \param metadata The metadata dictionary to write.
    #   \param file_name The virtual path of the JSON file to write to.
    def _writeMetadataToFile(self, metadata: Dict[str, Any], file_name: str) -> None:
        # Split the metadata into a hierarchical structure.
        document = {}
        for key, value in metadata.items():
            key = key.strip("/") #TODO: Should paths ending in a slash give an error?
            path = key.split("/")
            current_element = document
            for element in path:
                if element not in current_element:
                    current_element[element] = {}
                current_element = current_element[element]
            current_element[""] = value

        # We've created some empty-string keys to allow values to occur next to subelements.
        # If this empty-string key is the only key inside a node, fold it in to be just the value.
        for key in metadata:
            key = key.strip("/")
            path = key.split("/")
            current_element = document
            parent = document
            for element in path:
                parent = current_element
                current_element = current_element[element]
            if len(current_element) == 1: #The empty string is the only element.
                assert "" in current_element
                parent[path[-1]] = current_element[""] #Fold down the singleton dictionary.

        self.zipfile.writestr(file_name, json.dumps(document, sort_keys = True, indent = 4))

    ##  Helper function for pretty-printing XML because ETree is stupid.
    #
    #   Source: https://stackoverflow.com/questions/749796/pretty-printing-xml-in-python
    def _indent(self, elem, level = 0) -> None:
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self._indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i


##  Error to raise that something went wrong with reading/writing a UFP file.
class UFPError(Exception):
    pass  # This is just a marker class.
