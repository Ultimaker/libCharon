project(charon NONE)
cmake_minimum_required(VERSION 3.6) #Tested only with 3.6.1 and 3.9.1.

# Use FindPython 3 because if we use 3.4 for instance, it will prefer 3.4, even if there is another
# Python (say 3.5) in CMAKE_PREFIX_PATH which also meets the requirement. We prefer the Python in
# CMAKE_PREFIX_PATH if set for the Cura building process, so we specify Python 3 here.
find_package(PythonInterp 3 REQUIRED)

option(INSTALL_SERVICE "Install the Charon DBus-service" ON)
option(INSTALL_CLIENT "Install the Charon Client library" ON)

if(EXISTS /etc/debian_version)
    set(CHARON_INSTALL_PATH lib${LIB_SUFFIX}/python${PYTHON_VERSION_MAJOR}/dist-packages)
else()
    set(CHARON_INSTALL_PATH lib${LIB_SUFFIX}/python${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}/site-packages)
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
    COMMAND ${PYTHON_EXECUTABLE} -m pytest --junitxml=${CMAKE_BINARY_DIR}/junit-pytest-main.xml ${CMAKE_SOURCE_DIR}/tests
)
set_tests_properties(pytest-main PROPERTIES ENVIRONMENT LANG=C)
set_tests_properties(pytest-main PROPERTIES ENVIRONMENT "PYTHONPATH=${_PYTHONPATH}")
