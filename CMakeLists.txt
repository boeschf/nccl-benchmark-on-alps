cmake_minimum_required(VERSION 3.18)
project(nccl-tests LANGUAGES CXX)

# === C++ Standard ===
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# === CUDA Architecture Setting ===
set(CMAKE_CUDA_ARCHITECTURES "90" CACHE STRING "CUDA architectures")
string(REPLACE ";" "," CMAKE_CUDA_ARCH_LIST "${CMAKE_CUDA_ARCHITECTURES}")

# Construct the NVCC_GENCODE string based on CMAKE_CUDA_ARCHITECTURES
set(NVCC_GENCODE "")
foreach(arch IN LISTS CMAKE_CUDA_ARCHITECTURES)
    set(NVCC_GENCODE "${NVCC_GENCODE}-gencode=arch=compute_${arch},code=compute_${arch} ")
endforeach()
message(STATUS "NVCC_GENCODE=${NVCC_GENCODE}")

# === Options ===
option(DOWNLOAD_JOBREPORT "Download jobreport tool" ON)

# === Paths ===
list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}/bin CACHE PATH "Single Directory for all Executables.")
set(JOBREPORT_URL "https://github.com/eth-cscs/alps-jobreport/releases/download/v0.1/jobreport")
set(JOBREPORT_PATH "${CMAKE_SOURCE_DIR}/jobreport")

# === Dependency Management ===
include(FetchContent)
FetchContent_Declare(
    nccl-tests
    GIT_REPOSITORY https://github.com/NVIDIA/nccl-tests.git
    GIT_TAG origin/master
)
FetchContent_MakeAvailable(nccl-tests)

# === Optional: Download jobreport Tool ===
if (DOWNLOAD_JOBREPORT)
    if (NOT EXISTS ${JOBREPORT_PATH})
        message(STATUS "Downloading jobreport tool...")

        file(DOWNLOAD 
            ${JOBREPORT_URL}
            ${JOBREPORT_PATH}
            SHOW_PROGRESS
        )

        if (EXISTS ${JOBREPORT_PATH})
            file(CHMOD ${JOBREPORT_PATH} PERMISSIONS OWNER_EXECUTE OWNER_WRITE OWNER_READ)
            message(STATUS "jobreport tool downloaded and made executable.")
        else()
            message(FATAL_ERROR "Failed to download jobreport tool.")
        endif()
    else()
        message(STATUS "jobreport tool already exists in ${JOBREPORT_PATH}.")
    endif()
endif()

# === MPI Setup ===
find_package(MPI REQUIRED COMPONENTS CXX)
if (MPI_FOUND)
    get_target_property(MPI_LIBRARY_DIRS MPI::MPI_CXX INTERFACE_LINK_LIBRARIES)
    list(GET MPI_LIBRARY_DIRS 0 MPI_HOME)
    get_filename_component(MPI_HOME ${MPI_HOME} DIRECTORY)
    get_filename_component(MPI_HOME ${MPI_HOME} DIRECTORY)
    set(MPI_HOME "${MPI_HOME}" CACHE PATH "MPI root directory")
    message(STATUS "MPI_HOME = ${MPI_HOME}")
else()
    message(FATAL_ERROR "MPI not found")
endif()

# === CUDA Setup ===
find_package(CUDAToolkit REQUIRED)
if (CUDAToolkit_FOUND)
    get_target_property(CUDA_HOME CUDA::cudart IMPORTED_LOCATION)
    get_filename_component(CUDA_HOME ${CUDA_HOME} DIRECTORY)
    get_filename_component(CUDA_HOME ${CUDA_HOME} DIRECTORY)
    set(CUDA_HOME "${CUDA_HOME}" CACHE PATH "CUDA root directory")
    message(STATUS "CUDA_HOME = ${CUDA_HOME}")
else()
    message(FATAL_ERROR "CUDAToolkit not found")
endif()

# === NCCL Setup ===
find_package(nccl REQUIRED)
if (NCCL_FOUND)
    get_target_property(NCCL_HOME nccl::nccl IMPORTED_LOCATION)
    get_filename_component(NCCL_HOME ${NCCL_HOME} DIRECTORY)
    get_filename_component(NCCL_HOME ${NCCL_HOME} DIRECTORY)
    set(NCCL_HOME "${NCCL_HOME}" CACHE PATH "NCCL root directory")
    message(STATUS "NCCL_HOME = ${NCCL_HOME}")
else()
    message(FATAL_ERROR "NCCL not found")
endif()

# === nccl-tests build setup ===
set(NCCL_TESTS_BUILD_DIR ${CMAKE_BINARY_DIR}/nccl-tests-build)

# Get the number of available CPUs for parallel building
include(ProcessorCount)
ProcessorCount(NUM_CPUS)
if (NOT NUM_CPUS)
    set(NUM_CPUS 1)
endif()

# Build target for nccl-tests
add_custom_target(nccl-tests-build ALL
    COMMAND ${CMAKE_COMMAND} -E make_directory ${NCCL_TESTS_BUILD_DIR}
    COMMAND make -C ${nccl-tests_SOURCE_DIR} -j${NUM_CPUS} BUILDDIR=${NCCL_TESTS_BUILD_DIR} MPI=1 MPI_HOME=${MPI_HOME} CUDA_HOME=${CUDA_HOME} NCCL_HOME=${NCCL_HOME} CXX=${CMAKE_CXX_COMPILER}  NVCC_GENCODE="${NVCC_GENCODE}"
    COMMENT "Building nccl-tests with MPI, CUDA, and NCCL support using Makefile"
)

# Copy *_perf executables after the build
add_custom_command(TARGET nccl-tests-build
    POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_RUNTIME_OUTPUT_DIRECTORY}
    COMMAND ${CMAKE_COMMAND} -E copy ${NCCL_TESTS_BUILD_DIR}/*_perf ${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/
    COMMAND ${CMAKE_COMMAND} -E copy ${NCCL_TESTS_BUILD_DIR}/all_reduce_perf ${CMAKE_SOURCE_DIR}/
    COMMENT "Copying *_perf executables to ${CMAKE_RUNTIME_OUTPUT_DIRECTORY}"
)

# Additional Clean Files
set_directory_properties(PROPERTIES
    ADDITIONAL_MAKE_CLEAN_FILES "${NCCL_TESTS_BUILD_DIR}"
)

# Set nccl-tests as the main project
set_target_properties(nccl-tests-build PROPERTIES OUTPUT_NAME "nccl-tests")
