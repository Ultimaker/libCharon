project(charon)
cmake_minimum_required(VERSION 3.9.1) #Tested only with 3.9.1.

if(EXISTS /etc/debian_version)
    install(DIRECTORY Charon DESTINATION lib${LIB_SUFFIX}/python${PYTHON_VERSION_MAJOR}/dist-packages)
else()
    install(DIRECTORY Charon DESTINATION lib${LIB_SUFFIX}/python${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}/site-packages)
endif()

include(CPackConfig.cmake)