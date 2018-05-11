# Cura Packages
You can read and write a `.curapackage` file with ease using libCharon.

## Reading
You can create a new CuraPackage instance form an existing `.curapackage` file so it's easy to parse the contents.

```python
package = CuraPackage()
package.openStream(open("TestPackage.curapackage", "rb"))
```

After this, you can call the convinience methods on the package instance.

### Getting materials
You can get a list of available materials in the package using the `getMaterials` method.

```python
material_files = package.getMaterials()
```

This returns a list of full file paths relative to the package root.
You can then get the contents of any of the materials using the `read` method.

```python
for material_file_path in material_files:
    material_data = package.getStream(material_file_path)
```

This returns a `BytesIO` object to read the data from in the needed format.

## Writing
First, create a new package instance that we can write data to.

```python
stream = io.BytesIO()
package = CuraPackage()
package.openStream(stream, mode=OpenMode.WriteOnly)
```

After adding your data (see details below), don't forget to close the package.

```python
package.close()
```

### Adding materials
To add a material, you can use the `addMaterial` convinience method.
This will take care of the relationships, path alias and other implementation details of OPC.

```python
material_data = open("my_material.xml.fdm_material", "rb").read()
package.addMaterial(material_data=material_data, package_filename="my_material.xml.fdm_material")
```

### package.json
Each `.curapackage` has a `package.json` file with some metadata about the package.
LibCharon makes adding this metadata easy as well.

```python
package.setMetadata({"/package_id": "CharonTestPackage"})
```

This example added an entry to the JSON object as `{"package_id": "CharonTestPackage"}`.
