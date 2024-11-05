# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class PyTransformerEngine(PythonPackage, CudaPackage):
    """
    A library for accelerating Transformer models on NVIDIA GPUs, including fp8 precision on Hopper
    GPUs.
    """

    homepage = "https://github.com/NVIDIA/TransformerEngine"
    url = "https://github.com/NVIDIA/TransformerEngine/archive/refs/tags/v0.0.tar.gz"
    git = "https://github.com/NVIDIA/TransformerEngine.git"
    maintainers("aurianer")

    license("Apache-2.0")

    version("1.9.post1", commit="bdea56fc023014eaf52a171047b641b3bfdded70", submodules=True)
    version("1.9", tag="v1.9", submodules=True) 
    version("1.8", tag="v1.8", submodules=True) 
    version("1.6", tag="v1.6", submodules=True) 
    version("1.4", tag="v1.4", submodules=True)
    version("main", branch="main", submodules=True)

    depends_on("cxx", type="build")  # generated

    variant("userbuffers", default=True, description="Enable userbuffers, this option needs MPI.")

    depends_on("py-pydantic")
    depends_on("py-importlib-metadata")

    with default_args(type=("build")):
        depends_on("py-setuptools")
        depends_on("cmake@3.18:")
        depends_on("ninja")

    with default_args(type=("build", "run")):
        depends_on("py-accelerate")
        depends_on("py-datasets")
        depends_on("py-flash-attn@2.2:2.4.2", when="@:1.8,=1.9")
        depends_on("py-flash-attn@2.2:2.6.3", when="@=1.9.post1")
        depends_on("py-packaging")
        depends_on("py-torchvision")
        depends_on("py-transformers")
        depends_on("mpi", when="+userbuffers")

    with default_args(type=("build", "link", "run")):
        depends_on("py-pybind11")
        depends_on("py-torch+cuda+cudnn")
        depends_on("cudnn")

    def setup_build_environment(self, env):
        env.set("NVTE_FRAMEWORK", "pytorch")
        env.set("CUDNN_PATH", self.spec["cudnn"].prefix)
        env.set("CUDNN_HOME", self.spec["cudnn"].prefix)
        env.set("CUDNN_ROOT", self.spec["cudnn"].prefix)
        env.prepend_path("CPLUS_INCLUDE_PATH", self.spec["cudnn"].prefix.include)
        arch_str = ";".join(self.spec.variants["cuda_arch"].value)
        env.set("CUDAARCHS", arch_str)
        if self.spec.satisfies("+userbuffers"):
            env.set("NVTE_WITH_USERBUFFERS", "1")
            env.set("MPI_HOME", self.spec["mpi"].prefix)
