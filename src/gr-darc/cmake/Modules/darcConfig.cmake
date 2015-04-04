INCLUDE(FindPkgConfig)
PKG_CHECK_MODULES(PC_DARC darc)

FIND_PATH(
    DARC_INCLUDE_DIRS
    NAMES darc/api.h
    HINTS $ENV{DARC_DIR}/include
        ${PC_DARC_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    DARC_LIBRARIES
    NAMES gnuradio-darc
    HINTS $ENV{DARC_DIR}/lib
        ${PC_DARC_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
)

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(DARC DEFAULT_MSG DARC_LIBRARIES DARC_INCLUDE_DIRS)
MARK_AS_ADVANCED(DARC_LIBRARIES DARC_INCLUDE_DIRS)

