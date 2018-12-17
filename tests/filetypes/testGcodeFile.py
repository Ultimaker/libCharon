import io
import unittest

from Charon.filetypes.GCodeFile import GCodeFile


class TestGcodeFile(unittest.TestCase):

    def testGeneric(self) -> None:
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
            ";HEADER_VERSION:0.1\n" \
            ";TIME:11\n" \
            ";EXTRUDER_TRAIN.1.NOZZLE.DIAMETER:1.5\n" \
            ";EXTRUDER_TRAIN.1.MATERIAL.VOLUME_USED:1.5\n" \
            ";EXTRUDER_TRAIN.1.INITIAL_TEMPERATURE:666\n" \
            ";A.B.C:5\n" \
            ";END_OF_HEADER"

        gcode_stream = io.BytesIO(str.encode(gcode))
        metadata = GCodeFile.parseHeader(gcode_stream)

        self.assertEqual(metadata["a"]["b"]["c"], 5)
