# Copyright (c) 2018 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.
import ast

from typing import Any, Dict, IO, Optional

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
        self.__stream = None # type: Optional[IO[bytes]]
        self.__metadata = {} # type: Dict[str, Any]

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
                    metadata[key] = value

            if stream.seekable():
                stream.seek(0)

            flavor = metadata.get("flavor", None)
            if flavor == "Griffin":
                if metadata["header_version"] != "0.1":
                    raise InvalidHeaderException("Unsupported Griffin header version: {0}".format(metadata["header_version"]))

                metadata["machine_type"] = metadata["target_machine.name"]
                del metadata["target_machine.name"]

                if "generator.name" not in metadata or str(metadata["generator.name"]) == "":
                    raise InvalidHeaderException("GENERATOR.NAME must be set")
                if "generator.version" not in metadata or str(metadata["generator.version"]) == "":
                    raise InvalidHeaderException("GENERATOR.VERSION must be set")
                if "generator.build_date" not in metadata or str(metadata["generator.build_date"]) == "":
                    raise InvalidHeaderException("GENERATOR.BUILD_DATE must be set")

                generator_metadata = {}
                generator_metadata["name"] = metadata["generator.name"]
                generator_metadata["version"] = metadata["generator.version"]
                generator_metadata["build_date"] = metadata["generator.build_date"]
                metadata["generator"] = generator_metadata
                del metadata["generator.name"]
                del metadata["generator.version"]
                del metadata["generator.build_date"]

                if "build_plate.initial_temperature" not in metadata or not isAPositiveNumber(metadata["build_plate.initial_temperature"]):
                    raise InvalidHeaderException("BUILD_PLATE.INITIAL_TEMPERATURE must be set and be a positive real")

                metadata["build_plate"] ={}
                metadata["build_plate"]["initial_temperature"] = metadata["build_plate.initial_temperature"]
                del metadata["build_plate.initial_temperature"]

                if "build_plate.type" in metadata:
                    metadata["build_plate"]["type"] = metadata["build_plate.type"]
                    del metadata["build_plate.type"]

                if "print.size.min.x" not in metadata or "print.size.min.y" not in metadata or "print.size.min.z" not in metadata:
                    raise InvalidHeaderException("PRINT.SIZE.MIN.[x,y,z] must be set. Ensure all three are defined.")
                if "print.size.max.x" not in metadata or "print.size.max.y" not in metadata or "print.size.max.z" not in metadata:
                    raise InvalidHeaderException("PRINT.SIZE.MAX.[x,y,z] must be set. Ensure all three are defined.")

                metadata["print"] = {}

                min_size = {}
                min_size["x"] = metadata["print.size.min.x"]
                min_size["y"] = metadata["print.size.min.y"]
                min_size["z"] = metadata["print.size.min.z"]
                metadata["print"]["min_size"] = min_size
                del metadata["print.size.min.x"]
                del metadata["print.size.min.y"]
                del metadata["print.size.min.z"]

                max_size = {}
                max_size["x"] = metadata["print.size.max.x"]
                max_size["y"] = metadata["print.size.max.y"]
                max_size["z"] = metadata["print.size.max.z"]
                metadata["print"]["max_size"] = max_size
                del metadata["print.size.max.x"]
                del metadata["print.size.max.y"]
                del metadata["print.size.max.z"]

                if "time" in metadata:
                    metadata["print"]["time"] = metadata["time"]
                elif "print.time" in metadata:
                    metadata["print"]["time"] = metadata["print.time"]
                    del metadata["print.time"]
                else:
                    raise InvalidHeaderException("TIME or PRINT.TIME must be set")

                if int(metadata["print"]["time"]) < 0:
                    raise InvalidHeaderException("Print Time should be a positive integer")

                for index in range(0, 10):
                    extruder_key = "extruder_train.%s." % index
                    extruder_used = False
                    for key in metadata:
                        if extruder_key in key:
                            extruder_used = True
                            break

                    if not extruder_used:
                        continue

                    extruder_metadata = {}
                    nozzle_metadata = {}
                    material_metadata = {}

                    # Extruder is used. Ensure that all properties that must be set are set.
                    if extruder_key + "nozzle.diameter" not in metadata or not isAPositiveNumber(metadata[extruder_key + "nozzle.diameter"]):
                        raise InvalidHeaderException(extruder_key + "nozzle.diameter must be defined and be a positive real")
                    nozzle_metadata["diameter"] = metadata[extruder_key + "nozzle.diameter"]
                    del metadata[extruder_key + "nozzle.diameter"]

                    if extruder_key + "nozzle.name" in metadata:
                        nozzle_metadata["name"] = metadata[extruder_key + "nozzle.name"]
                        del metadata[extruder_key + "nozzle.name"]

                    extruder_metadata["nozzle"] = nozzle_metadata

                    if extruder_key + "material.volume_used" not in metadata or not isAPositiveNumber(metadata[extruder_key + "material.volume_used"]):
                        raise InvalidHeaderException(extruder_key + "material.volume_used must be defined and positive")
                    material_metadata["volume_used"] = metadata[extruder_key + "material.volume_used"]
                    del metadata[extruder_key + "material.volume_used"]

                    if extruder_key + "material.guid" in metadata:
                        material_metadata["guid"] = metadata[extruder_key + "material.guid"]
                        del metadata[extruder_key + "material.guid"]

                    extruder_metadata["material"] = material_metadata

                    initial_temp_key = extruder_key + "initial_temperature"
                    if initial_temp_key not in metadata or not isAPositiveNumber(metadata[initial_temp_key]):
                        raise InvalidHeaderException(initial_temp_key + " must be defined and be a positive real ")
                    extruder_metadata["initial_temperature"] = metadata[initial_temp_key]
                    del metadata[initial_temp_key]

                    if "extruders" not in metadata:
                        metadata["extruders"] = {}
                    metadata["extruders"][index] = extruder_metadata

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
