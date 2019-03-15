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


import pytest

import openfermion

import openfermioncirq as ofc
import openfermioncirq.testing.random  as ofctr
from openfermioncirq.primitives.general_swap_network import (
        trotterize)

@pytest.mark.parametrize('op', [ofctr.random_interaction_operator_term(k)
        for k in (1, 2, 3, 4) for _ in range(5)])
def test_random_interaction_operator_term_hermiticity(op):
    assert openfermion.is_hermitian(op)


@pytest.mark.parametrize('op', [ofctr.random_interaction_operator_term(k)
        for k in (1, 2, 3, 4) for _ in range(5)])
def test_random_interaction_operator_term_order(op):
    gates = trotterize(op)
    assert len(gates) == 1
    for key in gates:
        assert len(key) == len(op.one_body_tensor)
