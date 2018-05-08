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
import numpy
import pytest
import scipy.sparse.linalg

import cirq
from cirq import LineQubit
from openfermion import (
        count_qubits,
        fermi_hubbard,
        get_diagonal_coulomb_hamiltonian,
        get_sparse_operator)

from openfermioncirq.trotter import (
        SPLIT_OPERATOR, SWAP_NETWORK, simulate_trotter)


hubbard_hamiltonian = get_diagonal_coulomb_hamiltonian(
        fermi_hubbard(2, 2, 1., 4.))
complex_hamiltonian = get_diagonal_coulomb_hamiltonian(
        fermi_hubbard(2, 2, 1., 4.))
complex_hamiltonian.one_body += 1j * numpy.triu(complex_hamiltonian.one_body)
complex_hamiltonian.one_body -= 1j * numpy.tril(complex_hamiltonian.one_body)

@pytest.mark.parametrize(
        'hamiltonian, order, n_steps, algorithm, result_fidelity', [
            (hubbard_hamiltonian, 1, 2, SWAP_NETWORK, .97),
            (hubbard_hamiltonian, 1, 3, SWAP_NETWORK, .97),
            (hubbard_hamiltonian, 2, 1, SWAP_NETWORK, .97),
            (hubbard_hamiltonian, 1, 2, SPLIT_OPERATOR, .97),
            (hubbard_hamiltonian, 1, 3, SPLIT_OPERATOR, .97),
            (hubbard_hamiltonian, 2, 1, SPLIT_OPERATOR, .97),
            (complex_hamiltonian, 1, 3, SWAP_NETWORK, .97),
            (complex_hamiltonian, 1, 3, SPLIT_OPERATOR, .97),
])
def test_simulate_trotter(
        hamiltonian, order, n_steps, algorithm, result_fidelity):
    n_qubits = count_qubits(hamiltonian)

    # Get an eigenvalue and eigenvector
    hamiltonian_sparse = get_sparse_operator(hamiltonian)
    energies, states = scipy.sparse.linalg.eigsh(
            hamiltonian_sparse, k=1, which='SA')
    energy = energies[0]
    state = states[:, 0].astype(numpy.complex64, copy=False)
    assert numpy.allclose(numpy.linalg.norm(state), 1.0)

    # Simulate time evolution
    qubits = LineQubit.range(n_qubits)
    simulator = cirq.google.Simulator()
    time = abs(energy) / 5
    initial_state = state

    circuit = cirq.Circuit.from_ops(simulate_trotter(
        qubits, hamiltonian, time, n_steps, order, algorithm))
    result = simulator.run(
            circuit, qubit_order=qubits, initial_state=initial_state)
    final_state = result.final_states[0]

    # Hamiltonian evolution should simply apply a phase
    def fidelity(state1, state2):
        return abs(numpy.dot(state1, numpy.conjugate(state2)))
    assert fidelity(final_state, initial_state) > result_fidelity