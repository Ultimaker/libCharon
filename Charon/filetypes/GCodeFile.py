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

        flavor = metadata.get("flavor", "")
        if flavor == "Griffin":
            metadata["machine_type"] = metadata["target_machine.name"]
        elif flavor == "UltiGCode":
            metadata["machine_type"] = "ultimaker2"
        else:
            metadata["machine_type"] = "other"

        if "time" in metadata:
            metadata["print_time"] = metadata["time"]

        if "print.time" in metadata:
            metadata["print_time"] = metadata["print.time"]

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

        return {}

    def getStream(self, virtual_path):
        return self

    def close(self):
        self.__stream.close()
