project(charon NONE)
cmake_minimum_required(VERSION 3.6) #Tested only with 3.6.1 and 3.9.1.

# FIXME: Remove the code for CMake <3.12 once we have switched over completely.
# FindPython3 is a new module since CMake 3.12. It deprecates FindPythonInterp and FindPythonLibs.
if(${CMAKE_VERSION} VERSION_LESS 3.12)
    # Use FindPythonInterp and FindPythonLibs for CMake <3.12
    find_package(PythonInterp 3.4 REQUIRED)

    set(Python3_EXECUTABLE ${PYTHON_EXECUTABLE})
    set(Python3_VERSION_MAJOR ${PYTHON_VERSION_MAJOR})
    set(Python3_VERSION_MINOR ${PYTHON_VERSION_MINOR})
else()
    # Use FindPython3 for CMake >=3.12
    find_package(Python3 ${CURA_PYTHON_VERSION} EXACT REQUIRED COMPONENTS Interpreter)
endif()

option(INSTALL_SERVICE "Install the Charon DBus-service" ON)
option(INSTALL_CLIENT "Install the Charon Client library" ON)

if(EXISTS /etc/debian_version)
    set(CHARON_INSTALL_PATH lib${LIB_SUFFIX}/python${Python3_VERSION_MAJOR}/dist-packages)
else()
    set(CHARON_INSTALL_PATH lib${LIB_SUFFIX}/python${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}/site-packages)
endif()

set(_excludes PATTERN __pycache__ EXCLUDE)
if(NOT INSTALL_SERVICE)
    set(_excludes ${_excludes} PATTERN "Service" EXCLUDE)
endif()
if(NOT INSTALL_CLIENT)
    set(_excludes ${_excludes} PATTERN "Client" EXCLUDE)
endif()

install(DIRECTORY Charon DESTINATION ${CHARON_INSTALL_PATH} ${_excludes})

if(INSTALL_SERVICE)
    install(FILES service/charon.service DESTINATION lib/systemd/system)
    install(FILES service/nl.ultimaker.charon.conf DESTINATION share/dbus-1/system.d)
endif()

include(CPackConfig.cmake)

####################Loading the unit tests.###################
enable_testing()

include(CMakeParseArguments)

if(NOT _PYTHONPATH)
    set(_PYTHONPATH ${CMAKE_SOURCE_DIR})
endif()
if(WIN32)
    string(REPLACE "|" "\\;" _PYTHONPATH ${_PYTHONPATH})
    set(_PYTHONPATH "${_PYTHONPATH}\\;$ENV{PYTHONPATH}")
else()
    string(REPLACE "|" ":" _PYTHONPATH ${_PYTHONPATH})
    set(_PYTHONPATH "${_PYTHONPATH}:$ENV{PYTHONPATH}")
endif()

add_test(
    NAME pytest-main
    COMMAND ${Python3_EXECUTABLE} -m pytest --junitxml=${CMAKE_BINARY_DIR}/junit-pytest-main.xml ${CMAKE_SOURCE_DIR}/tests
)
set_tests_properties(pytest-main PROPERTIES ENVIRONMENT LANG=C)
set_tests_properties(pytest-main PROPERTIES ENVIRONMENT "PYTHONPATH=${_PYTHONPATH}")
