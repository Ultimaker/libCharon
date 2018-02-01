set(CPACK_PACKAGE_VENDOR "Ultimaker")
set(CPACK_PACKAGE_CONTACT "Ruben Dulek <r.dulek@ultimaker.com>")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Library to read and write file packages.")
set(CPACK_PACKAGE_VERSION_MAJOR 1)
set(CPACK_PACKAGE_VERSION_MINOR 0)
set(CPACK_PACKAGE_VERSION_PATCH 0)
set(CPACK_GENERATOR "DEB;RPM")

set(RPM_REQUIRES
    "python3 >= 3.5.0"
    "python3-qt5 >= 5.6.0"
    "qt5-qtgui >= 5.6.0"
)
string(REPLACE ";" "," RPM_REQUIRES "${RPM_REQUIRES}")
set(CPACK_RPM_PACKAGE_REQUIRES ${RPM_REQUIRES})

set(DEB_DEPENDS
    "python3 (>= 3.5.0)"
    "python3-pyqt5 (>= 5.6.0)"
    "python3-pyqt5.qtgui (>= 5.6.0)"
)
string(REPLACE ";" "," DEB_DEPENDS "${DEB_DEPENDS}")
set(CPACK_DEBIAN_PACKAGE_DEPENDS ${DEB_DEPENDS})

include(CPack)