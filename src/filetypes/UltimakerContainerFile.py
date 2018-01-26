# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.

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
    rels_file = "_rels/.rels" #Where the main relationships file is.
    content_types_file = "[Content_Types].xml" #Where the content types file is.

    def open(self, path: Optional[str] = None, mode: OpenMode = OpenMode.ReadOnly):
        self.mode = mode
        self.zipfile = zipfile.ZipFile(path, self.mode.value, compression = zipfile.ZIP_DEFLATED)
        self.metadata = {}

        #Load or create the content types element.
        self.content_types_element = None
        if self.content_types_file in self.zipfile.namelist():
            content_types_document = ET.fromstring(self.zipfile.open(self.content_types_file).read())
            content_types_element = content_types_document.find("Types")
            if content_types_element:
                self.content_types_element = content_types_element
        if not self.content_types_element:
            self.content_types_element = ET.Element("Types", xmlns = "http://schemas.openxmlformats.org/package/2006/content-types")
            if self.mode != OpenMode.ReadOnly:
                self._updateContentTypes()
        #If there is no type for the Rels file, create it.
        if self.mode != OpenMode.ReadOnly:
            for type_element in self.content_types_element.iterfind("Default"):
                if "Extension" in type_element.attrib and type_element.attrib["Extension"] == "rels":
                    break
            else:
                ET.SubElement(self.content_types_element, "Default", Extension = "rels", ContentType = "application/vnd.openxmlformats-package.relationships+xml")

        #Load or create the relations element.
        self.relations_element = None
        if self.rels_file in self.zipfile.namelist():
            relations_document = ET.fromstring(self.zipfile.open(self.rels_file).read())
            relations_element = relations_document.find("Relationships")
            if relations_element:
                self.relations_element = relations_element
        if not self.relations_element: #File didn't exist or didn't contain a Relationships element.
            self.relations_element = ET.Element("Relationships", xmlns = "http://schemas.openxmlformats.org/package/2006/relationships")
            if self.mode != OpenMode.ReadOnly:
                self._updateRels()

    def close(self):
        self.flush()
        self.zipfile.close()

    def flush(self):
        #Zipfile doesn't need flushing.
        pass

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

    def getStream(self, virtual_path):
        if self.mode == OpenMode.WriteOnly and virtual_path not in self.zipfile.namelist(): #File doesn't exist yet.
            self.zipfile.writestr(virtual_path, "")
            #TODO: Add manifest.

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
        self._updateContentTypes()

    ##  Adds a relation concerning a file type.
    #   \param virtual_path The target file that the relation is about.
    #   \param file_type The type of the target file. Any reader of UFP should
    #   be able to understand all types that are added via relations.
    def addRelation(self, virtual_path, file_type):
        if self.mode == OpenMode.ReadOnly:
            raise ReadOnlyError(virtual_path)

        #First check if it already exists.
        for relationship in self.relations_element.iterfind("Relationship"):
            if "Target" in relationship.attrib and relationship.attrib["Target"] == virtual_path:
                raise UFPError("Relation for virtual path {target} already exists.".format(target = virtual_path))

        #Find a unique name.
        unique_id = 0
        while self.relations_element.find("rel" + str(unique_id)):
            unique_id += 1
        unique_name = "rel" + str(unique_id)

        #Create the element itself.
        ET.SubElement(self.relations_element, "Relationship", Target = virtual_path, Type = file_type, Id = unique_name)
        self._updateRels()

    ##  When an element is added to the relations_element, we should update the
    #   rels file in the archive.
    #
    #   Make sure that self.relations_element is up to date first, then call
    #   this update function to actually update it in the file.
    def _updateRels(self):
        self.zipfile.writestr(self.rels_file, ET.tostring(self.xml_header) + "\n" + ET.tostring(self.relations_element))

    ##  When a content type is added to content_types_element, we should update
    #   the content types file in the archive.
    #
    #   Make sure that self.content_types_element is up to date first, then call
    #   this update function to actually update it in the file.
    def _updateContentTypes(self):
        self.zipfile.writestr(self.content_types_file, ET.tostring(self.xml_header) + "\n" + ET.tostring(self.content_types_element))

##  Error to raise that something went wrong with reading/writing a UFP file.
class UFPError(Exception):
    pass #This is just a marker class.