import io
import unittest

from Charon.filetypes.GCodeFile import GCodeFile, InvalidHeaderException


class TestGcodeFile(unittest.TestCase):

    __minimal_griffin_header = ";START_OF_HEADER\n" \
        ";FLAVOR:Griffin\n" \
        ";TARGET_MACHINE.NAME:target.foobar\n" \
        ";GENERATOR.NAME:generator_foo\n" \
        ";GENERATOR.VERSION: generator_version_foo\n" \
        ";GENERATOR.BUILD_DATE: generator_build_foo\n" \
        ";BUILD_PLATE.INITIAL_TEMPERATURE:30\n" \
        ";PRINT.SIZE.MIN.X:1\n" \
        ";PRINT.SIZE.MIN.Y:2\n" \
        ";PRINT.SIZE.MIN.Z:3\n" \
        ";PRINT.SIZE.MAX.X:1\n" \
        ";PRINT.SIZE.MAX.Y:2\n" \
        ";PRINT.SIZE.MAX.Z:3\n" \
        ";HEADER_VERSION:0.1\n" \
        ";TIME:11\n" \
        ";EXTRUDER_TRAIN.1.NOZZLE.DIAMETER:1.5\n" \
        ";EXTRUDER_TRAIN.1.MATERIAL.VOLUME_USED:1.5\n" \
        ";EXTRUDER_TRAIN.1.INITIAL_TEMPERATURE:666\n" \
        "{}\n" \
        ";END_OF_HEADER"

    def _print(self, d, prefix=""):
        for k, v in d.items():
            if type(v) is dict:
                self._print(v, prefix="{}.{}".format(prefix, k) if prefix else "{}".format(k))
            else:
                if prefix:
                    print("{}.{}: {}".format(prefix, k, v))
                else:
                    print("{}: {}".format(k, v))

    def testParseGenericParameter_HappyTrail(self) -> None:
        gcode = self.__minimal_griffin_header.format(";A.B.C:5")
        gcode_stream = io.BytesIO(str.encode(gcode))
        metadata = GCodeFile.parseHeader(gcode_stream)

        self._print(metadata)  # print if any assert fails
        self.assertEqual(metadata["a"]["b"]["c"], 5)
        self.assertEqual(metadata["generator"]["name"], "generator_foo")
        self.assertEqual(metadata["build_plate"]["initial_temperature"], 30)
        self.assertEqual(metadata["extruders"][1]["nozzle"]["diameter"], 1.5)
        self.assertEqual(metadata["print"]["time"], 11)
        self.assertEqual(metadata["time"], 11)  # This was the behavior of the old code.

    def testParseHeader_MissingFlavor(self) -> None:
        gcode = ";START_OF_HEADER\n" \
            ";TARGET_MACHINE.NAME:target.foobar\n" \
            ";GENERATOR.NAME:generator_foo\n" \
            ";GENERATOR.VERSION: generator_version_foo\n" \
            ";GENERATOR.BUILD_DATE: generator_build_foo\n" \
            ";BUILD_PLATE.INITIAL_TEMPERATURE:30\n" \
            ";PRINT.SIZE.MIN.X:1\n" \
            ";PRINT.SIZE.MIN.Y:2\n" \
            ";PRINT.SIZE.MIN.Z:3\n" \
            ";PRINT.SIZE.MAX.X:1\n" \
            ";PRINT.SIZE.MAX.Y:2\n" \
            ";PRINT.SIZE.MAX.Z:3\n" \
            ";HEADER_VERSION:0.1\n" \
            ";TIME:11\n"

        self.__parseWithInvalidHeaderException(gcode, "Flavor")

    def testParseHeader_MissingHeaderVersion(self) -> None:
        gcode = ";START_OF_HEADER\n" \
            ";FLAVOR:Griffin\n" \
            ";TARGET_MACHINE.NAME:target.foobar\n" \
            ";GENERATOR.NAME:generator_foo\n" \
            ";GENERATOR.VERSION: generator_version_foo\n" \
            ";GENERATOR.BUILD_DATE: generator_build_foo\n" \
            ";BUILD_PLATE.INITIAL_TEMPERATURE:30\n" \
            ";PRINT.SIZE.MIN.X:1\n" \
            ";PRINT.SIZE.MIN.Y:2\n" \
            ";PRINT.SIZE.MIN.Z:3\n" \
            ";PRINT.SIZE.MAX.X:1\n" \
            ";PRINT.SIZE.MAX.Y:2\n" \
            ";PRINT.SIZE.MAX.Z:3\n" \
            ";TIME:11\n"

        self.__parseWithInvalidHeaderException(gcode, "version")

    def testParseHeader_MissingTargetMachine(self) -> None:
        gcode = ";START_OF_HEADER\n" \
            ";FLAVOR:Griffin\n" \
            ";GENERATOR.NAME:generator_foo\n" \
            ";GENERATOR.VERSION: generator_version_foo\n" \
            ";GENERATOR.BUILD_DATE: generator_build_foo\n" \
            ";BUILD_PLATE.INITIAL_TEMPERATURE:30\n" \
            ";PRINT.SIZE.MIN.X:1\n" \
            ";PRINT.SIZE.MIN.Y:2\n" \
            ";PRINT.SIZE.MIN.Z:3\n" \
            ";PRINT.SIZE.MAX.X:1\n" \
            ";PRINT.SIZE.MAX.Y:2\n" \
            ";PRINT.SIZE.MAX.Z:3\n" \
            ";HEADER_VERSION:0.1\n" \
            ";TIME:11\n"
        self.__parseWithInvalidHeaderException(gcode, "TARGET_MACHINE")

    def testParseHeader_MissingGeneratorName(self) -> None:
        gcode = ";START_OF_HEADER\n" \
            ";FLAVOR:Griffin\n" \
            ";TARGET_MACHINE.NAME:target.foobar\n" \
            ";GENERATOR.VERSION: generator_version_foo\n" \
            ";GENERATOR.BUILD_DATE: generator_build_foo\n" \
            ";BUILD_PLATE.INITIAL_TEMPERATURE:30\n" \
            ";PRINT.SIZE.MIN.X:1\n" \
            ";PRINT.SIZE.MIN.Y:2\n" \
            ";PRINT.SIZE.MIN.Z:3\n" \
            ";PRINT.SIZE.MAX.X:1\n" \
            ";PRINT.SIZE.MAX.Y:2\n" \
            ";PRINT.SIZE.MAX.Z:3\n" \
            ";HEADER_VERSION:0.1\n" \
            ";TIME:11\n"
        self.__parseWithInvalidHeaderException(gcode, "GENERATOR.NAME")

    def testParseHeader_MissingGeneratorVersion(self) -> None:
        gcode = ";START_OF_HEADER\n" \
            ";FLAVOR:Griffin\n" \
            ";TARGET_MACHINE.NAME:target.foobar\n" \
            ";GENERATOR.NAME:generator_foo\n" \
            ";GENERATOR.BUILD_DATE: generator_build_foo\n" \
            ";BUILD_PLATE.INITIAL_TEMPERATURE:30\n" \
            ";PRINT.SIZE.MIN.X:1\n" \
            ";PRINT.SIZE.MIN.Y:2\n" \
            ";PRINT.SIZE.MIN.Z:3\n" \
            ";PRINT.SIZE.MAX.X:1\n" \
            ";PRINT.SIZE.MAX.Y:2\n" \
            ";PRINT.SIZE.MAX.Z:3\n" \
            ";HEADER_VERSION:0.1\n" \
            ";TIME:11\n"
        self.__parseWithInvalidHeaderException(gcode, "GENERATOR.VERSION")

    def testParseHeader_MissingGeneratorBuildDate(self) -> None:
        gcode = ";START_OF_HEADER\n" \
            ";FLAVOR:Griffin\n" \
            ";TARGET_MACHINE.NAME:target.foobar\n" \
            ";GENERATOR.NAME:generator_foo\n" \
            ";GENERATOR.VERSION: generator_version_foo\n" \
            ";BUILD_PLATE.INITIAL_TEMPERATURE:30\n" \
            ";PRINT.SIZE.MIN.X:1\n" \
            ";PRINT.SIZE.MIN.Y:2\n" \
            ";PRINT.SIZE.MIN.Z:3\n" \
            ";PRINT.SIZE.MAX.X:1\n" \
            ";PRINT.SIZE.MAX.Y:2\n" \
            ";PRINT.SIZE.MAX.Z:3\n" \
            ";HEADER_VERSION:0.1\n" \
            ";TIME:11\n"
        self.__parseWithInvalidHeaderException(gcode, "GENERATOR.BUILD_DATE")

    def testParseHeader_MissingInitialBuildPlateTemp(self) -> None:
        gcode = ";START_OF_HEADER\n" \
            ";FLAVOR:Griffin\n" \
            ";TARGET_MACHINE.NAME:target.foobar\n" \
            ";GENERATOR.NAME:generator_foo\n" \
            ";GENERATOR.VERSION: generator_version_foo\n" \
            ";GENERATOR.BUILD_DATE: generator_build_foo\n" \
            ";PRINT.SIZE.MIN.X:1\n" \
            ";PRINT.SIZE.MIN.Y:2\n" \
            ";PRINT.SIZE.MIN.Z:3\n" \
            ";PRINT.SIZE.MAX.X:1\n" \
            ";PRINT.SIZE.MAX.Y:2\n" \
            ";PRINT.SIZE.MAX.Z:3\n" \
            ";HEADER_VERSION:0.1\n" \
            ";TIME:11\n"

        self.__parseWithInvalidHeaderException(gcode, "BUILD_PLATE.INITIAL_TEMPERATURE")

    def testParseHeader_MissingMinSizeX(self) -> None:
        gcode = ";START_OF_HEADER\n" \
            ";FLAVOR:Griffin\n" \
            ";TARGET_MACHINE.NAME:target.foobar\n" \
            ";GENERATOR.NAME:generator_foo\n" \
            ";GENERATOR.VERSION: generator_version_foo\n" \
            ";GENERATOR.BUILD_DATE: generator_build_foo\n" \
            ";BUILD_PLATE.INITIAL_TEMPERATURE:30\n" \
            ";PRINT.SIZE.MIN.Y:2\n" \
            ";PRINT.SIZE.MIN.Z:3\n" \
            ";PRINT.SIZE.MAX.X:1\n" \
            ";PRINT.SIZE.MAX.Y:2\n" \
            ";PRINT.SIZE.MAX.Z:3\n" \
            ";HEADER_VERSION:0.1\n" \
            ";TIME:11\n"

        self.__parseWithInvalidHeaderException(gcode, "PRINT.SIZE.MIN")

    def testParseHeader_MissingMaxSizeZ(self) -> None:
        gcode = ";START_OF_HEADER\n" \
            ";FLAVOR:Griffin\n" \
            ";TARGET_MACHINE.NAME:target.foobar\n" \
            ";GENERATOR.NAME:generator_foo\n" \
            ";GENERATOR.VERSION: generator_version_foo\n" \
            ";GENERATOR.BUILD_DATE: generator_build_foo\n" \
            ";BUILD_PLATE.INITIAL_TEMPERATURE:30\n" \
            ";PRINT.SIZE.MIN.X:1\n" \
            ";PRINT.SIZE.MIN.Y:2\n" \
            ";PRINT.SIZE.MIN.Z:3\n" \
            ";PRINT.SIZE.MAX.X:1\n" \
            ";PRINT.SIZE.MAX.Y:2\n" \
            ";HEADER_VERSION:0.1\n" \
            ";TIME:11\n"

        self.__parseWithInvalidHeaderException(gcode, "PRINT.SIZE.MAX")

    def testParseHeader_MissingPrintTime(self) -> None:
        gcode = ";START_OF_HEADER\n" \
            ";FLAVOR:Griffin\n" \
            ";TARGET_MACHINE.NAME:target.foobar\n" \
            ";GENERATOR.NAME:generator_foo\n" \
            ";GENERATOR.VERSION: generator_version_foo\n" \
            ";GENERATOR.BUILD_DATE: generator_build_foo\n" \
            ";BUILD_PLATE.INITIAL_TEMPERATURE:30\n" \
            ";PRINT.SIZE.MIN.X:1\n" \
            ";PRINT.SIZE.MIN.Y:2\n" \
            ";PRINT.SIZE.MIN.Z:3\n" \
            ";PRINT.SIZE.MAX.X:1\n" \
            ";PRINT.SIZE.MAX.Y:2\n" \
            ";PRINT.SIZE.MAX.Z:3\n" \
            ";HEADER_VERSION:0.1\n"

        self.__parseWithInvalidHeaderException(gcode, "TIME")
        self.__parseWithInvalidHeaderException(gcode, "PRINT.TIME")

    def __parseWithInvalidHeaderException(self, gcode, text) -> None: 
        gcode_stream = io.BytesIO(str.encode(gcode))
        
        with self.assertRaises(InvalidHeaderException) as cm:
            metadata = GCodeFile.parseHeader(gcode_stream)
        self.assertTrue(text  in str(cm.exception))

    def testParseGenericParameter_NoValue(self) -> None:
        gcode = self.__minimal_griffin_header.format(";A.B.C:")
        gcode_stream = io.BytesIO(str.encode(gcode))
        metadata = GCodeFile.parseHeader(gcode_stream)

        self.assertEqual(metadata["a"]["b"]["c"], '')

