# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.

from io import BufferedIOBase #For the type of input of open_stream.
import json #The metadata format.
from typing import Any, Dict, Optional
import xml.etree.ElementTree as ET #For writing XML manifest files.
import zipfile

from ..FileInterface import FileInterface #The interface we're implementing.
from ..OpenMode import OpenMode #To detect whether we want to read and/or write to the file.
from ..ReadOnlyError import ReadOnlyError #To be thrown when trying to write while in read-only mode.

##  A container file type that contains multiple 3D-printing related files that
#   belong together.
class UltimakerContainerFile(FileInterface):
    #Some constants related to this format.
    xml_header = ET.ProcessingInstruction("xml", "version=\"1.0\" encoding=\"UTF-8\"") #Header element being put atop every XML file.
    global_rels_file = "_rels/.rels" #Where the global relationships file is.
    content_types_file = "[Content_Types].xml" #Where the content types file is.
    global_metadata_file = "Metadata/UCF_Global.json" #Where the global metadata file is.

    def open_stream(self, stream: BufferedIOBase, mime: str, mode: OpenMode = OpenMode.ReadOnly):
        self.mode = mode
        self.zipfile = zipfile.ZipFile(stream, self.mode.value, compression = zipfile.ZIP_DEFLATED)
        self.metadata = {}

        #Load or create the content types element.
        self.content_types_element = None
        self._readContentTypes()

        #Load or create the relations.
        self.relations = {} #For each virtual path, a relations XML element (which is left out if empty).
        self._readRels()

    def close(self):
        self.flush()
        self.zipfile.close()

    def flush(self):
        if self.mode == OpenMode.ReadOnly:
            return #No need to flush reading of zip archives as they are blocking calls.
        self._writeMetadata() #Metadata must be updated first, because that adds rels and a content type.
        self._writeContentTypes()
        self._writeRels()

    def getMetadata(self, virtual_path: str) -> Dict[str, Any]:
        #Find all metadata that begins with the specified virtual path!
        result = {}

        if virtual_path in self.metadata: #The exact match.
            result[virtual_path] = self.metadata[virtual_path]
        for entry_path, value in self.metadata.items():
            #We only want to match subdirectories of the provided virtual paths.
            #So if you provide "/foo" then we don't want to match on "/foobar"
            #but we do want to match on "/foo/zoo". This is why we check if they
            #start with the provided virtual path plus a slash.
            if entry_path.startswith(virtual_path + "/"):
                result[entry_path] = value
        return result

    def setMetadata(self, metadata: Dict[str, Any]):
        self.metadata.update(metadata)

    def getStream(self, virtual_path):
        return self.zipfile.open(virtual_path, self.mode.value)

    def toByteArray(self, offset: int = 0, count: int = -1):
        with open(self.zipfile.filename, "b") as f:
            if offset > 0:
                f.seek(offset)
            return f.read(count)

    ##  Adds a new content type to the archive.
    #   \param extension The file extension of the type
    def addContentType(self, extension, mime_type):
        if self.mode == OpenMode.ReadOnly:
            raise ReadOnlyError()

        #First check if it already exists.
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
    def addRelation(self, virtual_path: str, relation_type: str, origin: str = ""):
        if self.mode == OpenMode.ReadOnly:
            raise ReadOnlyError(virtual_path)

        #First check if it already exists.
        if origin not in self.relations:
            self.relations[origin] = ET.Element("Relationships", xmlns = "http://schemas.openxmlformats.org/package/2006/relationships")
        else:
            for relationship in self.relations[origin].iterfind("Relationship"):
                if "Target" in relationship.attrib and relationship.attrib["Target"] == virtual_path:
                    raise UFPError("Relation for virtual path {target} already exists.".format(target = virtual_path))

        #Find a unique name.
        unique_id = 0
        while True:
            for relationship in self.relations[origin].iterfind("Relationship"):
                if "Id" in relationship.attrib and relationship.attrib["Id"] == "rel" + str(unique_id):
                    break
            else: #Unique ID didn't exist yet! It's safe to use
                break
            unique_id += 1
        unique_name = "rel" + str(unique_id)

        #Create the element itself.
        ET.SubElement(self.relations[origin], "Relationship", Target = virtual_path, Type = relation_type, Id = unique_name)

    ##  When loading a file, load the relations from the archive.
    #
    #   If the relations are missing, empty elements are created.
    def _readRels(self):
        if self.global_rels_file not in self.zipfile.namelist(): #There must always be a global Relationships document.
            self.relations[""] = ET.Element("Relationships", xmlns = "http://schemas.openxmlformats.org/package/2006/relationships")

        #Below is some parsing of paths and extensions.
        #Normally you'd use os.path for this. But this is platform-dependent.
        #For instance, the path separator in Windows is a backslash, but zipfile still uses a slash on Windows.
        #So instead we have custom implementations here. Sorry.

        for virtual_path in self.zipfile.namelist():
            if not virtual_path.endswith(".rels"): #We only want to read rels files.
                continue
            if "/" not in virtual_path: #No slash at all. It can't be in the "_rels" directory.
                continue
            directory = virtual_path[:virtual_path.rfind("/")] #Before the last slash.
            if directory != "_rels" and not directory.endswith("/_rels"): #Rels files must be in a directory _rels.
                continue

            document = ET.fromstring(self.zipfile.open(virtual_path).read())
            relations_element = document.find("Relationships")

            #Find out what file or directory this relation is about.
            origin_filename = virtual_path[virtual_path.rfind("/") + 1:-len(".rels")] #Just the filename (no path) and without .rels extension.
            origin_directory = directory[:-len("/_rels")] #The parent path. We already know it's in the _rels directory.
            origin = (origin_directory + "/" if (origin_directory != "") else "") + origin_filename

            self.relations[origin] = relations_element

    ##  At the end of writing a file, write the relations to the archive.
    #
    #   This should be written at the end of writing an archive, when all
    #   relations are known.
    def _writeRels(self):
        #Below is some parsing of paths and extensions.
        #Normally you'd use os.path for this. But this is platform-dependent.
        #For instance, the path separator in Windows is a backslash, but zipfile still uses a slash on Windows.
        #So instead we have custom implementations here. Sorry.

        for origin, element in self.relations.items():
            #Find out where to store the rels file.
            if "/" not in origin: #Is in root.
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
    def _readContentTypes(self):
        if self.content_types_file in self.zipfile.namelist():
            content_types_document = ET.fromstring(self.zipfile.open(self.content_types_file).read())
            content_types_element = content_types_document.find("Types")
            if content_types_element:
                self.content_types_element = content_types_element
        if not self.content_types_element:
            self.content_types_element = ET.Element("Types", xmlns = "http://schemas.openxmlformats.org/package/2006/content-types")
        #If there is no type for the Rels file, create it.
        if self.mode != OpenMode.ReadOnly:
            for type_element in self.content_types_element.iterfind("Default"):
                if "Extension" in type_element.attrib and type_element.attrib["Extension"] == "rels":
                    break
            else:
                ET.SubElement(self.content_types_element, "Default", Extension = "rels", ContentType = "application/vnd.openxmlformats-package.relationships+xml")

    ##  At the end of writing a file, write the content types to the archive.
    #
    #   This should be written at the end of writing an archive, when all
    #   content types are known.
    def _writeContentTypes(self):
        self._indent(self.content_types_element)
        self.zipfile.writestr(self.content_types_file, ET.tostring(self.xml_header) + b"\n" + ET.tostring(self.content_types_element))

    ##  At the end of writing a file, write the metadata to the archive.
    #
    #   This should be written at the end of writing an archive, when all
    #   metadata is known.
    #
    #   ALWAYS WRITE METADATA BEFORE UPDATING RELS AND CONTENT TYPES.
    def _writeMetadata(self):
        keys_left = set(self.metadata.keys()) #The keys that are not associated with a particular file (global metadata).
        metadata_per_file = {}
        for file_name in self.zipfile.namelist():
            metadata_per_file[file_name] = {}
            for metadata_key in self.metadata:
                if metadata_key.startswith(file_name + "/"):
                    #Strip the prefix: "/a/b/c.stl/print_time" becomes just "print_time" about the file "/a/b/c.stl".
                    metadata_per_file[file_name][metadata_key[len(file_name) + 1:]] = self.metadata[metadata_key]
                    keys_left.remove(metadata_key)
        #keys_left now contains only global metadata keys.

        global_metadata = {key:self.metadata[key] for key in keys_left}
        if len(global_metadata) > 0:
            self._writeMetadataToFile(global_metadata, self.global_metadata_file)
            self.addRelation(self.global_metadata_file, "http://schemas.ultimaker.org/package/2018/relationships/ucf_metadata")
        for file_name, metadata in metadata_per_file.items():
            if len(metadata) > 0:
                self._writeMetadataToFile(metadata, file_name + ".json")
                self.addRelation(file_name + ".json", "http://schemas.ultimaker.org/package/2018/relationships/ucf_metadata")
        if len(self.metadata) > 0: #If we've written any metadata at all, we must include the content type as well.
            try:
                self.addContentType(extension = "json", mime_type = "text/json")
            except UFPError: #User may already have defined this content type himself.
                pass

    ##  Writes one dictionary of metadata to a JSON file.
    #   \param metadata The metadata dictionary to write.
    #   \param file_name The virtual path of the JSON file to write to.
    def _writeMetadataToFile(self, metadata: Dict[str, Any], file_name: str):
        #Split the metadata into a hierarchical structure.
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

        #We've created some empty-string keys to allow values to occur next to subelements.
        #If this empty-string key is the only key inside a node, fold it in to be just the value.
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
    def _indent(self, elem, level = 0):
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
    pass #This is just a marker class.