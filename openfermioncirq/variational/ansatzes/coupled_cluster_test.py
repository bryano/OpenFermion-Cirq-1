#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import itertools
import random

import cirq
import cirq.contrib.acquaintance as cca
import numpy as np
import openfermion

import pytest

from openfermioncirq.primitives.general_swap_network import (
    trotter_unitary)
from openfermioncirq.variational.ansatzes.coupled_cluster import (
    CoupledClusterOperator,
    PairedCoupledClusterOperator,
    UnitaryCoupledClusterAnsatz)


def test_cc_operator():
    pass


@pytest.mark.parametrize('n_spatial_modes',
    range(2, 7))
def test_paired_cc_operator(n_spatial_modes):
    for kwargs in (dict(zip(['include_real_part', 'include_imag_part'], flags))
            for flags in itertools.product((True, False), repeat=2)):
        operator = PairedCoupledClusterOperator(n_spatial_modes, **kwargs)
        params = list(operator.params())
        assert len(set(params)) == len(params)
        assert len(params) == (
                n_spatial_modes * (n_spatial_modes - 1) * sum(kwargs.values()))
        T = operator.operator()
        H = T - openfermion.hermitian_conjugated(T)
        resolver = {p: random.uniform(-5, 5) for p in operator.params()}
        H = cirq.resolve_parameters(H, resolver)
        exponent = 1j * H
        assert (not exponent) or openfermion.is_hermitian(exponent)


def print_hermitian_matrices(*matrices):
    matrices = tuple(matrices)
    assert len(set(m.shape for m in matrices)) == 1
    N = len(matrices[0])
    n = int(np.log2(N))
    assert N == 1 << n
    for i, j in itertools.combinations_with_replacement(range(N), 2):
        vs = tuple(matrix[i, j] for matrix in matrices)
        if any(vs):
            line = '{0:0{n}b} {1:0{n}b} '.format(i, j, n=n)
            line += ' '.join('{}'.format(v) for v in vs)
            print(line)


def random_resolver(operator):
    return {p: random.uniform(-5, 5) for p in operator.params()}


@pytest.mark.parametrize('cluster_operator,resolver',
    [(cluster_operator, random_resolver(cluster_operator))
        for n_spatial_modes in [2, 3, 4]
        for cluster_operator in [PairedCoupledClusterOperator(n_spatial_modes,
            include_real_part=False)]
        for _ in range(3)
        ])
def test_paired_ucc(cluster_operator, resolver):
    ansatz = UnitaryCoupledClusterAnsatz(cluster_operator)

    circuit = cirq.resolve_parameters(ansatz._circuit, resolver)

    swap_network = cluster_operator.swap_network()

    actual_unitary = circuit.to_unitary_matrix(
            qubit_order=swap_network.qubit_order)

    acquaintance_dag = cca.get_acquaintance_dag(
            swap_network.circuit, swap_network.initial_mapping)
    operator = cluster_operator.operator()
    resolved_operator = cirq.resolve_parameters(operator, resolver)
    hamiltonian = -1j * (resolved_operator -
            openfermion.hermitian_conjugated(resolved_operator))
    expected_unitary = trotter_unitary(acquaintance_dag, hamiltonian)

    assert np.allclose(actual_unitary, expected_unitary)
