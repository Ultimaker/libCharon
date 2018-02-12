import ast

from ..FileInterface import FileInterface
from ..OpenMode import OpenMode


class GCodeFile(FileInterface):
    is_binary = False

    MaximumHeaderLength = 100

    def __init__(self):
        self.__stream = None
        self.__metadata = {}

    def openStream(self, stream, mime, mode):
        if mode != OpenMode.ReadOnly:
            raise NotImplementedError()

        self.__stream = stream
        self.__metadata = {}
        self.__metadata = self.parseHeader(self.__stream, prefix = "/metadata/toolpath/default/")

    @staticmethod
    def parseHeader(stream, *, prefix = ""):
        metadata = {}
        line_number = 0
        for line_number, line in enumerate(stream):
            if line_number > GCodeFile.MaximumHeaderLength:
                break

            if line.startswith(";START_OF_HEADER"):
                continue
            elif line.startswith(";LAYER") or line.startswith(";END_OF_HEADER"):
                break
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
            metadata["machine_type"] = metadata["target_machine.name"]

            if "generator.name" not in metadata:
                raise InvalidHeaderException("GENERATOR.NAME must be set")
            if "generator.version" not in metadata:
                raise InvalidHeaderException("GENERATOR.VERSION must be set")
            if "generator.build_date" not in metadata:
                raise InvalidHeaderException("GENERATOR.BUILD_DATE must be set")
            if "build_plate.initial_temperature" not in metadata:
                raise InvalidHeaderException("GENERATOR.INITIAL_TEMPERATURE must be set")
            if "print.size.min.x" not in metadata or "print.size.min.y" not in metadata or "print.size.min.z" not in metadata:
                raise InvalidHeaderException("GENERATOR.SIZE.MIN.[x,y,z] must be set. Ensure all three are defined.")
            if "print.size.max.x" not in metadata or "print.size.max.y" not in metadata or "print.size.max.z" not in metadata:
                raise InvalidHeaderException("GENERATOR.SIZE.MAX.[x,y,z] must be set. Ensure all three are defined.")

            for index in range(0, 10):
                extruder_key = "extruder_train.%s." % index
                extruder_used = False
                for key in metadata:
                    if extruder_key in key:
                        extruder_used = True
                        break

                if not extruder_used:
                    continue

                # Extruder is used. Ensure that all properties that must be set are set.
                if extruder_key + "nozzle.diameter" not in metadata:
                    raise InvalidHeaderException(extruder_key + "nozzle.diameter must be defined")

                if extruder_key + "material.volume_used" not in metadata:
                    raise InvalidHeaderException(extruder_key + "material.volume_used must be defined")

                if extruder_key + "initial_temperature" not in metadata:
                    raise InvalidHeaderException(extruder_key + "initial_temperature must be defined")

        elif flavor == "UltiGCode":
            metadata["machine_type"] = "ultimaker2"
        else:
            raise InvalidHeaderException("Flavor must be defined!")

        if "time" in metadata:
            metadata["print_time"] = metadata["time"]
        elif "print.time" in metadata:
            metadata["print_time"] = metadata["print.time"]
        else:
            raise InvalidHeaderException("TIME or PRINT.TIME must be set")

        if "print.size.min.x" in metadata:
            print_volume = {}
            print_volume["width"] = metadata["print.size.max.x"] - metadata["print.size.min.x"]
            print_volume["height"] = metadata["print.size.max.z"] - metadata["print.size.min.z"]
            print_volume["depth"] = metadata["print.size.max.y"] - metadata["print.size.min.y"]
            metadata["print_size"] = print_volume

        if prefix:
            prefixed_metadata = {}
            for key, value in metadata.items():
                prefixed_metadata[prefix + key] = value
            metadata = prefixed_metadata

        return metadata

    def getData(self, virtual_path):
        if virtual_path.startswith("/metadata"):
            result = {}
            for key, value in self.__metadata.items():
                if key.startswith(virtual_path):
                    result[key] = value
            return result

        if virtual_path == "/toolpath" or virtual_path == "/toolpath/default":
            return { virtual_path: self.__stream.read() }

        return {}

    def getStream(self, virtual_path):
        if virtual_path != "/toolpath" and virtual_path != "/toolpath/default":
            raise NotImplementedError("GCode files only support /toolpath as stream")

        return self.__stream

    def close(self):
        self.__stream.close()


class InvalidHeaderException(Exception):
    pass