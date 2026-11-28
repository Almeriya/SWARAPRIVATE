# SwaraXT — third-party dependencies at the caller-supplied path.

set(SWARAXT_JUCE_DIR "${CMAKE_SOURCE_DIR}/.cache/JUCE" CACHE PATH
    "Path to the JUCE source root")

if(NOT EXISTS "${SWARAXT_JUCE_DIR}/CMakeLists.txt")
    message(FATAL_ERROR
        "JUCE not found at ${SWARAXT_JUCE_DIR}. Set SWARAXT_JUCE_DIR to a supported checkout")
endif()

if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    include("${CMAKE_CURRENT_LIST_DIR}/LinuxJuce904Identity.cmake")
    swaraxt_verify_linux_juce904("${SWARAXT_JUCE_DIR}")
    set(swaraxt_juce_version_regex "project\\(JUCE VERSION 9\\.0\\.4")
    set(swaraxt_juce_version_name "9.0.4")
else()
    set(swaraxt_juce_version_regex "project\\(JUCE VERSION 9\\.0\\.1")
    set(swaraxt_juce_version_name "9.0.1")
endif()

file(STRINGS "${SWARAXT_JUCE_DIR}/CMakeLists.txt" swaraxt_juce_project_line
     REGEX "${swaraxt_juce_version_regex}")
if(NOT swaraxt_juce_project_line)
    message(FATAL_ERROR "SWARAXT_JUCE_DIR must point to JUCE ${swaraxt_juce_version_name}")
endif()

set(JUCE_WEB_BROWSER 0 CACHE BOOL "Disable JUCE WebBrowser module" FORCE)
set(JUCE_BUILD_EXTRAS OFF CACHE BOOL "" FORCE)
set(JUCE_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)

add_subdirectory("${SWARAXT_JUCE_DIR}" "${CMAKE_BINARY_DIR}/JUCE" EXCLUDE_FROM_ALL)

if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    include("${CMAKE_CURRENT_LIST_DIR}/LinuxJuce904Compatibility.cmake")
elseif(WIN32 OR APPLE)
    # Pinned JUCE 9.0.1 (e18f7f506c0b96f2c738a0bcd7fe6467a5005ad8) stores APVTS
    # sources as CRLF. GitHub-hosted bytes match the verified Windows overlay
    # input hashes, and Juce901RestoreCompletion.patch applies with the same
    # output hashes. Enable the build-local overlay on Apple; keep the MSVC
    # libpng longjmp overlay Windows-only.
    include("${CMAKE_CURRENT_LIST_DIR}/Juce901RestoreCompletion.cmake")
    if(WIN32)
        include("${CMAKE_CURRENT_LIST_DIR}/Juce901PngError.cmake")
    endif()
endif()
