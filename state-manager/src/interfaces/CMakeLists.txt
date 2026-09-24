cmake_minimum_required(VERSION 3.15)
if(NOT PROJECT_NAME)
  project(interfaces)
endif()

set(OBC_GS_INTERFACE_LIB_NAME obc-gs-interface)

set(INCLUDE_DIRS
  ${CMAKE_CURRENT_SOURCE_DIR}/obc_gs_interface/common
  ${CMAKE_CURRENT_SOURCE_DIR}/obc_gs_interface/commands/inc
  ${CMAKE_CURRENT_SOURCE_DIR}/obc_gs_interface/telemetry
  ${CMAKE_CURRENT_SOURCE_DIR}/obc_gs_interface/aes128
  ${CMAKE_CURRENT_SOURCE_DIR}/obc_gs_interface/ax25
  ${CMAKE_CURRENT_SOURCE_DIR}/obc_gs_interface/fec

  ${CMAKE_CURRENT_SOURCE_DIR}/data_pack_unpack
)

set(SOURCES
  ${CMAKE_CURRENT_SOURCE_DIR}/data_pack_unpack/data_pack_utils.c
  ${CMAKE_CURRENT_SOURCE_DIR}/data_pack_unpack/data_unpack_utils.c

  ${CMAKE_CURRENT_SOURCE_DIR}/obc_gs_interface/commands/src/obc_gs_command_pack.c
  ${CMAKE_CURRENT_SOURCE_DIR}/obc_gs_interface/commands/src/obc_gs_command_unpack.c
  ${CMAKE_CURRENT_SOURCE_DIR}/obc_gs_interface/telemetry/obc_gs_telemetry_pack.c
  ${CMAKE_CURRENT_SOURCE_DIR}/obc_gs_interface/telemetry/obc_gs_telemetry_unpack.c

  ${CMAKE_CURRENT_SOURCE_DIR}/obc_gs_interface/commands/src/obc_gs_commands_response_pack.c
  ${CMAKE_CURRENT_SOURCE_DIR}/obc_gs_interface/commands/src/obc_gs_commands_response_unpack.c

  ${CMAKE_CURRENT_SOURCE_DIR}/obc_gs_interface/aes128/obc_gs_aes128.c
  ${CMAKE_CURRENT_SOURCE_DIR}/obc_gs_interface/ax25/obc_gs_ax25.c
  ${CMAKE_CURRENT_SOURCE_DIR}/obc_gs_interface/fec/obc_gs_fec.c

  ${CMAKE_CURRENT_SOURCE_DIR}/obc_gs_interface/common/obc_gs_crc.c
  ${CMAKE_CURRENT_SOURCE_DIR}/gs_heap/gs_heap.c
)

list(APPEND INCLUDE_DIRS ${CMAKE_CURRENT_SOURCE_DIR}/interface_libs/libcorrect/include)

add_library(${OBC_GS_INTERFACE_LIB_NAME} SHARED ${SOURCES})

target_include_directories(${OBC_GS_INTERFACE_LIB_NAME} PUBLIC ${INCLUDE_DIRS})

add_subdirectory(interface_libs)

target_link_libraries(${OBC_GS_INTERFACE_LIB_NAME} PRIVATE
    tiny-aes
    lib-correct
)
