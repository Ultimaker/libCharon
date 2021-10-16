set(CPACK_PACKAGE_VENDOR "Ultimaker")
set(CPACK_PACKAGE_CONTACT "Ultimaker <plugins@ultimaker.com>")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Library to read and write 3D printer related files including G-Code and Ultimaker File Package.")
set(CPACK_PACKAGE_VERSION_MAJOR 1)
set(CPACK_PACKAGE_VERSION_MINOR 0)
set(CPACK_PACKAGE_VERSION_PATCH 0)
set(CPACK_GENERATOR "DEB")

set(CPACK_DEBIAN_PACKAGE_ARCHITECTURE all)

set(DEB_DEPENDS
    "python3 (>= 3.4.2)"
    "python3-dbus (>= 1.2.0)"
    "dbus (>= 1.8.0)"
)
string(REPLACE ";" "," DEB_DEPENDS "${DEB_DEPENDS}")
set(CPACK_DEBIAN_PACKAGE_DEPENDS ${DEB_DEPENDS})
set(CPACK_DEBIAN_PACKAGE_CONTROL_EXTRA "${CMAKE_CURRENT_SOURCE_DIR}/service/postinst")

include(CPack)
