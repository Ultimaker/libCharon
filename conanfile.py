import os
import pathlib

from conans import ConanFile


required_conan_version = ">=1.42"


class CharonConan(ConanFile):
    name = "charon"
    version = "5.0.0"
    license = "LGPL-3.0"
    author = "Ultimaker B.V."
    url = "https://github.com/Ultimaker/libCharon"
    description = "File metadata and streaming library"
    topics = ("conan", "python", "cura", "ufp")
    settings = "os", "compiler", "build_type", "arch"
    revision_mode = "scm"
    build_policy = "missing"
    default_user = "ultimaker"
    default_channel = "testing"
    exports = "LICENSE*"
    python_requires = ["UltimakerBase/0.1@ultimaker/testing"]
    python_requires_extend = "UltimakerBase.UltimakerBase"
    no_copy_source = True

    scm = {
        "type": "git",
        "subfolder": ".",
        "url": "auto",
        "revision": "auto"
    }

    def package(self):
        self.copy("*.py", src = "Charon", dst = os.path.join("site-packages", "Charon"))

    def package_info(self):
        if self.in_local_cache:
            self.runenv_info.prepend_path("PYTHONPATH", os.path.join(self.package_folder, "site-packages"))
        else:
            self.runenv_info.prepend_path("PYTHONPATH", str(pathlib.Path(__file__).parent.absolute()))

    def package_id(self):
        self.info.header_only()
