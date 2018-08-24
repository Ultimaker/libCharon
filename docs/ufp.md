Ultimaker Format Package (UFP)
============

Purpose:
--------
The goal of this file type is to provide required data for the 3D printer to perform a print job.

Structure:
--------
A UFP file contains the following files:
`\.rels`
`\Metadata\thumbnail.png`
`\Cura\`
`\3D\model.gcode`
`\[Content_Types].xml`
1) The rels and content type files are filled with the required XML data.
2) The thumbnail.png is a medium sized rendering of the 3D shape to show during file selection. There can be only one thumbnail.
3) The model.gcode describes how a 3D printer should print a job.
4) Possible content of Cura folder :
- *.xml.fdm_material – files describe materials specifications which might be needed for a print job.

Notes:
-------------
- For the interchange of files between the Slicer and Printers, currently, ASCII GCODE files are used, in a specific Ultimaker flavor.
- In future development, the content of folder Cura might be changed. 
