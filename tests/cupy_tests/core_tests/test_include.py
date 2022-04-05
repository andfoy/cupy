import os
from unittest import mock

import cupy

import pytest


_code_base = '''
#include <cuda_fp16.h>

#include <cupy/carray.cuh>
#include <cupy/complex.cuh>
#include <cupy/cuComplex_bridge.h>
#include <cupy/math_constants.h>
#include <cupy/atomics.cuh>
#include <cupy/hip_workaround.cuh>
#include <cupy/swap.cuh>
#include <cupy/tuple.cuh>
'''

_code_nvcc = _code_base + '''
#include <cupy/type_dispatcher.cuh>

int main() {
    return 0;
}
'''

_code_nvrtc = _code_base + '''

__device__ void kernel() {
}
'''


@pytest.mark.skipif(cupy.cuda.runtime.is_hip, reason='for CUDA')
class TestIncludesCompileCUDA:
    def _get_cuda_archs(self):
        cuda_ver = cupy.cuda.runtime.runtimeGetVersion()
        if cuda_ver < 11000:
            # CUDA 10.2
            archs = (30, 32, 35, 50, 52, 53, 60, 61, 62, 70, 72, 75)
        elif cuda_ver < 11010:
            # CUDA 11.0
            archs = (35, 37, 50, 52, 53, 60, 61, 62, 70, 72, 75, 80)
        elif cuda_ver < 11020:
            # CUDA 11.1
            archs = (35, 37, 50, 52, 53, 60, 61, 62, 70, 72, 75, 80, 86)
        else:
            # CUDA 11.2+.
            archs = cupy.cuda.nvrtc.getSupportedArchs()
        return archs

    def _get_options(self):
        return (
            '-I{}'.format(cupy._core.core._get_header_dir_path()),
            '-I{}'.format(os.path.join(cupy.cuda.get_cuda_path(), 'include')),
        )

    def test_nvcc(self):
        options = self._get_options()
        for arch in self._get_cuda_archs():
            cupy.cuda.compiler.compile_using_nvcc(
                _code_nvcc, options=options, arch=arch)

    def test_nvrtc(self):
        options = self._get_options()
        for arch in self._get_cuda_archs():
            with mock.patch(
                    'cupy.cuda.compiler._get_arch_for_options_for_nvrtc',
                    lambda _: (f'-arch=compute_{arch}', 'ptx')):
                cupy.cuda.compiler.compile_using_nvrtc(
                    _code_nvrtc, options=options)
            with mock.patch(
                    'cupy.cuda.compiler._get_arch_for_options_for_nvrtc',
                    lambda _: (f'-arch=sm_{arch}', 'cubin')):
                cupy.cuda.compiler.compile_using_nvrtc(
                    _code_nvrtc, options=options)
