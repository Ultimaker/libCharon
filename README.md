# libCharon
File metadata and streaming library

See docs/library.md for details.

## Usage as library
Read a gcode file:
```
from Charon.VirtualFile import VirtualFile

f = VirtualFile()
f.open("file.gcode")
print(f.getData("/metadata"))
for line in f.getStream("/toolpath"):
    print(line)
f.close()
```

Create a UltimakerFormatPackage (UFP)
```
from Charon.VirtualFile import VirtualFile
from Charon.OpenMode import OpenMode

f = VirtualFile()
f.open("output.ufp", OpenMode.WriteOnly)
f.setData("/toolpath", "TEST123")
f.close()
```

## Usage as service
TODO
