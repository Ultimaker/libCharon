project(charon)
cmake_minimum_required(VERSION 3.6.1) #Tested only with 3.6.1 and 3.9.1.

find_package(PythonInterp 3.5.0 REQUIRED)

if(EXISTS /etc/debian_version)
    install(DIRECTORY Charon DESTINATION lib${LIB_SUFFIX}/python${PYTHON_VERSION_MAJOR}/dist-packages)
else()
    install(DIRECTORY Charon DESTINATION lib${LIB_SUFFIX}/python${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}/site-packages)
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