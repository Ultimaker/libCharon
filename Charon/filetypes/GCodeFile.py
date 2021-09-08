# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.
import ast

from typing import Any, Dict, IO, List, Optional, Union

from Charon.FileInterface import FileInterface
from Charon.OpenMode import OpenMode


def isAPositiveNumber(a: str) -> bool:
    try:
        number = float(repr(a))
        return number >= 0
    except:
        bool_a = False

    return bool_a


class GCodeFile(FileInterface):
    mime_type = "text/x-gcode"

    MaximumHeaderLength = 100

    def __init__(self) -> None:
        self.__stream = None  # type: Optional[IO[bytes]]
        self.__metadata = {}  # type: Dict[str, Any]

    def openStream(self, stream: IO[bytes], mime: str, mode: OpenMode = OpenMode.ReadOnly) -> None:
        if mode != OpenMode.ReadOnly:
            raise NotImplementedError()

        self.__stream = stream
        self.__metadata = {}
        self.__metadata = self.parseHeader(self.__stream, prefix = "/metadata/toolpath/default/")

    @staticmethod
    def parseHeader(stream: IO[bytes], *, prefix: str = "") -> Dict[str, Any]:
        try:
            metadata = {} # type: Dict[str, Any]
            line_number = 0
            for line_number, bytes_line in enumerate(stream):
                if line_number > GCodeFile.MaximumHeaderLength:
                    break
                line = bytes_line.decode("utf-8")

                if line.startswith(";START_OF_HEADER"):
                    continue
                elif line.startswith(";LAYER") or line.startswith(";END_OF_HEADER"):
                    break
                elif line.startswith(";HEADER_VERSION"):
                    # Header version is a number but should not be parsed as number, so special case it.
                    metadata["header_version"] = line.split(":")[1].strip()
                elif line.startswith(";") and ":" in line:
                    key, value = line[1:].split(":")
                    key = key.strip().lower()
                    value = value.strip()
                    try:
                        value = ast.literal_eval(value.strip())
                    except:
                        pass
                    key_elements = key.split(".")
                    GCodeFile.__insertKeyValuePair(metadata, key_elements, value)
            
            if stream.seekable():
                stream.seek(0)

            flavor = metadata.get("flavor", None)
            if flavor == "Griffin":
                if metadata["header_version"] != "0.1":
                    raise InvalidHeaderException("Unsupported Griffin header version: {0}".format(metadata["header_version"]))
                GCodeFile.__validateGriffinHeader(metadata)
                GCodeFile.__cleanGriffinHeader(metadata)
            elif flavor == "UltiGCode":
                metadata["machine_type"] = "ultimaker2"
            else:
                raise InvalidHeaderException("Flavor must be defined!")

            if prefix:
                prefixed_metadata = {}
                for key, value in metadata.items():
                    prefixed_metadata[prefix + key] = value
                metadata = prefixed_metadata

            return metadata
        except Exception as e:
            raise InvalidHeaderException("Unable to parse the header. An exception occured; %s" % e)


    ## Add a key-value pair to the metadata dictionary.
    # Splits up key each element to it's own dictionary.
    # @param metadata Metadata collection
    # @param key_elements List of separate key name elements
    # @param value Key value
    @staticmethod
    def __insertKeyValuePair(
        metadata: Dict[str, Any],
        key_elements: Any,
        value: Any
    ) -> Any:
        if not key_elements:
            return value 

        sub_dict = {}

        if key_elements[0] in metadata:
            sub_dict = metadata[key_elements[0]]

        metadata[key_elements[0]] = GCodeFile.__insertKeyValuePair(sub_dict, key_elements[1:], value)
       
        return metadata    

    def getData(self, virtual_path: str) -> Dict[str, Any]:
        assert self.__stream is not None

        if virtual_path.startswith("/metadata"):
            result = {}
            for key, value in self.__metadata.items():
                if key.startswith(virtual_path):
                    result[key] = value
            return result

        if virtual_path == "/toolpath" or virtual_path == "/toolpath/default":
            return { virtual_path: self.__stream.read() }

        return {}

    ## Cleans a parsed GRIFFIN flavoured GCODE header.
    @staticmethod
    def __cleanGriffinHeader(metadata: Dict[str, Any]) -> None:
        metadata["machine_type"] = metadata["target_machine"]["name"]
        del metadata["target_machine"]
    
        if GCodeFile.__isAvailable(metadata, ["time"]):
            GCodeFile.__insertKeyValuePair(metadata, ["print", "time"], metadata["time"])
            # del metadata["time"]  # We want to delete the old key, but it's behavior of how the code was.

        GCodeFile.__insertKeyValuePair(metadata, ["print", "min_size"], metadata["print"]["size"]["min"])
        GCodeFile.__insertKeyValuePair(metadata, ["print", "max_size"], metadata["print"]["size"]["max"])
        del metadata["print"]["size"]
        
        for key, value in metadata["extruder_train"].items():
            GCodeFile.__insertKeyValuePair(metadata, ["extruders", int(key)], value)

        del metadata["extruder_train"]

    ## Checks if a path to a key is available
    # @param metadata Metadata collection to check for the presence of the key
    # @param keys List of key elements describing the path to a value. If a key element is a list, then all the elements
    #             must exist on the location of that key element
    # @return True if the key is available and not empty
    @staticmethod
    def __isAvailable(metadata: Dict[str, Any], keys: List[Any]) -> bool:
        if not keys:
            return True

        key = keys[0]
        
        if isinstance(key, list):
            key_is_valid = True
            for sub_key in key:
                key_is_valid = key_is_valid and GCodeFile.__isAvailable(metadata, [sub_key] + [keys[1:]])
        else:
            key_is_valid = key in metadata and metadata[key] is not None and not str(metadata[key]) == ""
            key_is_valid = key_is_valid and GCodeFile.__isAvailable(metadata[key], keys[1:])

        return key_is_valid
    
    ## Validates a parsed GRIFFIN flavoured GCODE header.
    # Will raise an InvalidHeader exception when the header is invalid.
    # @param metadata Key/value dictionary based on the header.
    @staticmethod
    def __validateGriffinHeader(metadata: Dict[str, Any]) -> None:

        # Validate target settings
        if not GCodeFile.__isAvailable(metadata, ["target_machine", "name"]): 
            raise InvalidHeaderException("TARGET_MACHINE.NAME must be set")

        # Validate generator settings
        if not GCodeFile.__isAvailable(metadata, ["generator", "name"]): 
            raise InvalidHeaderException("GENERATOR.NAME must be set")
        if not GCodeFile.__isAvailable(metadata, ["generator", "version"]): 
            raise InvalidHeaderException("GENERATOR.VERSION must be set")
        if not GCodeFile.__isAvailable(metadata, ["generator", "build_date"]): 
            raise InvalidHeaderException("GENERATOR.BUILD_DATE must be set")

        # Validate build plate temperature 
        if not GCodeFile.__isAvailable(metadata, ["build_plate", "initial_temperature"]) or \
            not isAPositiveNumber(metadata["build_plate"]["initial_temperature"]):
            raise InvalidHeaderException("BUILD_PLATE.INITIAL_TEMPERATURE must be set and be a positive real")
      
        # Validate dimensions 
        if not GCodeFile.__isAvailable(metadata, ["print", "size", "min", ["x", "y", "z"]]):
            raise InvalidHeaderException("PRINT.SIZE.MIN.[x,y,z] must be set. Ensure all three are defined.")
        if not GCodeFile.__isAvailable(metadata, ["print", "size", "max", ["x", "y", "z"]]):
            raise InvalidHeaderException("PRINT.SIZE.MAX.[x,y,z] must be set. Ensure all three are defined.")
        
        # Validate print time
        print_time = -1

        if GCodeFile.__isAvailable(metadata, ["print", "time"]):
            print_time = int(metadata["print"]["time"])
        elif GCodeFile.__isAvailable(metadata, ["time"]):
            print_time = int(metadata["time"])
        else:
            raise InvalidHeaderException("TIME or PRINT.TIME must be set")

        if print_time < 0:
            raise InvalidHeaderException("Print Time should be a positive integer")
       
        # Validate extruder train
        for index in range(0, 10):
            index_str = str(index)
            if GCodeFile.__isAvailable(metadata, ["extruder_train", index_str]):

                if not GCodeFile.__isAvailable(metadata, ["extruder_train", index_str, "nozzle", "diameter"]) or \
                    not isAPositiveNumber(metadata["extruder_train"][index_str]["nozzle"]["diameter"]):
                        raise InvalidHeaderException(
                            "extruder_train.{}.nozzle.diameter must be defined and be a positive real".format(index))
       
                if not GCodeFile.__isAvailable(metadata, ["extruder_train", index_str, "material", "volume_used"]) or \
                    not isAPositiveNumber(metadata["extruder_train"][index_str]["material"]["volume_used"]):
                        raise InvalidHeaderException(
                            "extruder_train.{}.material.volume_used must be defined and positive".format(index))

                if not GCodeFile.__isAvailable(metadata, ["extruder_train", index_str, "initial_temperature"]) or \
                    not isAPositiveNumber(metadata["extruder_train"][index_str]["initial_temperature"]):
                        raise InvalidHeaderException(
                            "extruder_train.{}.initial_temperature must be defined and positive".format(index))

    def getStream(self, virtual_path: str) -> IO[bytes]:
        assert self.__stream is not None
        
        if virtual_path != "/toolpath" and virtual_path != "/toolpath/default":
            raise NotImplementedError("G-code files only support /toolpath as stream")

        return self.__stream

    def close(self) -> None:
        assert self.__stream is not None
        
        self.__stream.close()


class InvalidHeaderException(Exception):
    pass
