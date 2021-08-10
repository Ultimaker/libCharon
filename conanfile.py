import os
import pathlib

from conans import ConanFile
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake

class CharonConan(ConanFile):
    name = "Charon"
    version = "4.10.0"
    license = "LGPL-3.0"
    author = "Ultimaker B.V."
    url = "https://github.com/Ultimaker/libCharon"
    description = "File metadata and streaming library"
    topics = ("conan", "python", "cura", "ufp")
    settings = "os", "compiler", "build_type", "arch"
    exports = "LICENSE"
    options = {
        "python_version": "ANY"
    }
    default_options = {
        "python_version": "3.8"
    }
    scm = {
        "type": "git",
        "subfolder": ".",
        "url": "auto",
        "revision": "auto"
    }

    def build_requirements(self):
        self.build_requires("cmake/[>=3.16.2]")

    def generate(self):
        cmake = CMakeDeps(self)
        cmake.generate()

        tc = CMakeToolchain(self)
        tc.variables["CURA_PYTHON_VERSION"] = self.options.python_version
        tc.generate()

    _cmake = None

    def configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self)
        self._cmake.configure()
        return self._cmake

    def build(self):
        cmake = self.configure_cmake()
        cmake.build()

    def package(self):
        cmake = self.configure_cmake()
        cmake.install()
        self.copy("*", src = os.path.join("package", "lib", f"python{self.options.python_version}", "site-packages"), dst = "site-packages")

    def package_info(self):
        if self.in_local_cache:
            self.runenv_info.prepend_path("PYTHONPATH", os.path.join(self.package_folder, "site-packages"))
        else:
            self.runenv_info.prepend_path("PYTHONPATH", str(pathlib.Path(__file__).parent.absolute()))

    def package_id(self):
        self.info.header_only()
