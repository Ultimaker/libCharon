# Copyright (c) 2019 Ultimaker B.V.
# libCharon is released under the terms of the LGPLv3 or higher.

import setuptools

setuptools.setup(
    name = "libCharon",
    use_scm_version=True,
    description = "Library to read and write file packages.",
    author = "Ultimaker",
    author_email = "r.dulek@ultimaker.com",
    url = "https://github.com/Ultimaker/libCharon",
    packages = ["Charon", "Charon.Client", "Charon.Service", "Charon.filetypes"],
    setup_requires=['setuptools_scm']
)
