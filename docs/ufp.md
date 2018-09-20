# Ultimaker Format Package (UFP)

The Ultimaker Format package is an OPC (Open Package Convention) based file format. It's designed to allow for various other payloads, apart from the "default" toolpath that is provided by a regular g-code file. The initial implementation / release of this standard allows for thumbnails and toolpath metadata to be added. Future versions might include more payloads such as material files. UFP files should always describe a single "print job".

## Forwards compatible with 3MF
One of the main features of UFP is that it's fully forwards compatible with 3MF.

The main reason to not directly extend 3MF with the functionality Ultimaker needs on their printer is due to storage constraints. UFP is intended to be lighter / smaller than 3MF, since 3MF forces the 3D model data of the print job to be a part of the file.

However, we do expect that this will no longer be an issue with future generations of printers. As such, we have made UFP forwards compatible with 3MF. This makes it possible for older machines to accept 3MF files that have an UFP extension, without needing to update them.

## Structure
### Required files
* `.rels` The root relations file, which describes the relations of the package as a whole.
* `Metadata/thumbnail.png` An png tumbnail (300x300px) of the 3D model that is to be printed
* `3D/model.gcode` The actual toolpath that needs to be printed.
* `[Content_Types].xml` Definitions of all the MIME types stored in the package.

### Optional files
* `Materials/*.xml.fdm_material` 0-n material files, which describe the material that the toolpath was sliced with. If this is a material that is unknown to the 3D printer that recieves this print-job it could add this material to it's database for future reference / automatic NFC detection.
* `Materials/*.xml.fdm_material.sig` 0-n signature files. Ultimaker 3D printers, from the UM3 and upwards, support the signing of material files. Since unknown materials could be added to the internal database of the machine, it might need to be signed if this is a protected material profile.
