import ast

from ..FileInterface import FileInterface
from ..OpenMode import OpenMode

class GCodeFile(FileInterface):
    is_binary = False

    #MaximumHeaderStartLines = 50
    MaximumHeaderLength = 100

    def __init__(self):
        self.__stream = None
        self.__metadata = {}

    def openStream(self, stream, mime, mode):
        if mode != OpenMode.ReadOnly:
            raise NotImplementedError()

        self.__stream = stream
        self.__metadata = {}
        metadata = self.parseHeader(self.__stream)
        for key, value in metadata.items():
            self.__metadata["/metadata/toolpath/default/" + key] = value

        print(self.__metadata)

    @staticmethod
    def parseHeader(stream):
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

        return metadata

    def getData(self, virtual_path):
        if virtual_path.startswith("/metadata"):
            return self.__metadata
        if virtual_path.startswith("/toolpath"):
            return self.__stream.read()

        return {}

    def getStream(self, virtual_path):
        return self

    def close(self):
        self.__stream.close()
