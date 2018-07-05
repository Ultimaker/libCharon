# Ultimaker Format Package (UFP)

Create a UltimakerFormatPackage
```
from Charon.VirtualFile import VirtualFile
from Charon.OpenMode import OpenMode

f = VirtualFile()
f.open("output.ufp", OpenMode.WriteOnly)
f.setData("/toolpath", "TEST123")
f.close()
```
