# Copyright (c) 2018 Ultimaker B.V.	
# libCharon is released under the terms of the LGPLv3 or higher.	

from distutils.core import setup	

setup(	
    name = "Charon",	
    version = "1.0",	
    description = "Library to read and write file packages.",	
    author = "Ultimaker",	
    author_email = "plugins@ultimaker.com",
    url = "https://github.com/Ultimaker/libCharon",	
    packages = ["Charon", "Charon.Client", "Charon.Service", "Charon.filetypes"]	
)
