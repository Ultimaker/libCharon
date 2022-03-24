project(charon NONE)
cmake_minimum_required(VERSION 3.18)

if(NOT DEFINED Python_VERSION)
    set(Python_VERSION
            3.10
            CACHE STRING "Python Version" FORCE)
    message(STATUS "Setting Python version to ${Python_VERSION}. Set Python_VERSION if you want to compile against an other version.")
endif()
if(APPLE)
    set(Python_FIND_FRAMEWORK NEVER)
endif()
find_package(Python ${Python_VERSION} EXACT REQUIRED COMPONENTS Interpreter)
message(STATUS "Linking and building ${project_name} against Python ${Python_VERSION}")
if(NOT DEFINED Python_SITELIB_LOCAL)
    set(Python_SITELIB_LOCAL
            "${Python_SITELIB}"
            CACHE PATH "Local alternative site-package location to install Cura" FORCE)
endif()

option(INSTALL_SERVICE "Install the Charon DBus-service" ON)
option(INSTALL_CLIENT "Install the Charon Client library" ON)

install(DIRECTORY Charon DESTINATION "${Python_SITELIB_LOCAL}")

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
    COMMAND ${Python_EXECUTABLE} -m pytest --junitxml=${CMAKE_BINARY_DIR}/junit-pytest-main.xml ${CMAKE_SOURCE_DIR}/tests
)
set_tests_properties(pytest-main PROPERTIES ENVIRONMENT LANG=C)
set_tests_properties(pytest-main PROPERTIES ENVIRONMENT "PYTHONPATH=${_PYTHONPATH}")
