# Cura Packages
You can read and write a `.curapackage` file with ease using libCharon.

## Writing
First, create a new package instance that we can write data to.

```python
stream = io.BytesIO()
package = CuraPackage()
package.openStream(stream, mode = OpenMode.WriteOnly)
```

After adding your data (see details below), don't forget to close the package.

```python
package.close()
```

### Adding materials
To add a material, you can use the `addMaterial` convinience method.
This will take care of the relationships, path alias and other implementation details of OPC.

```python
material_file = open(os.path.join("my_material.xml.fdm_material", "rb").read()
package.addMaterial(original_material, filename)
```

### package.json
Each `.curapackage` has a `package.json` file with some metadata about the package.
LibCharon makes adding this metadata easy as well.

```python
package.setMetadata({"/package_id": "CharonTestPackage"})
```

This example added an entry to the JSON object as `{"package_id": "CharonTestPackage"}`.
