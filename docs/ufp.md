<h1>Ultimaker Format Package (UFP)</h1>

<h3>Purpose:</h3>

The goal of this file type is to provide required data for the 3D printer to perform a print job.

<h3>Structure:</h3>

A UFP file contains the following files:</br>
`\.rels`</br>
`\Metadata\thumbnail.png`</br>
`\Cura\`</br>
`\3D\model.gcode`</br>
`\[Content_Types].xml`</br>

<ul>
  <li>The rels and content type files are filled with the required XML data.</li>
  <li>The thumbnail.png is a medium sized rendering of the 3D shape to show during file selection. There can be only one thumbnail.</li>
  <li>The model.gcode describes how a 3D printer should print a job.</li>
  <li>Possible content of Cura folder :</br>
    <ul>
      <li>*.xml.fdm_material – files describe materials specifications which might be needed for a print job./li>
    </ul>
  </li>
</ul>

<h3>Notes:</h3>

- For the interchange of files between the Slicer and Printers, currently, ASCII GCODE files are used, in a specific Ultimaker flavor.
- In future development, the content of folder Cura might be changed. 
