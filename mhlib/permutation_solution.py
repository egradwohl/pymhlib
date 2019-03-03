"""A generic solution class for solutions that are represented by permutations of integers."""

import numpy as np
from abc import ABC

from mhlib.solution import VectorSolution


class PermutationSolution(VectorSolution, ABC):
    """Solution that is represented by a permutation of 0,...length-1."""

    def __init__(self, length: int, init=True, **kwargs):
        """Initializes the solution with 0,...,length-1 if init is set."""
        super().__init__(length, init=False, **kwargs)
        if init:
            self.x[:] = np.arange(length)

    def copy_from(self, other: 'PermutationSolution'):
        super().copy_from(other)

    def initialize(self, k):
        """Random initialization."""
        np.random.shuffle(self.x)

    def check(self):
        """Check if valid solution.

        :raises ValueError: if problem detected.
        """
        super().check()
        if set(self.x) != set(range(len(self.x))):
            raise ValueError("Solution is no permutation of 0,...,length-1")

    def two_exchange_neighborhood_search(self, best_improvement) -> bool:
        """Perform the systematic search of the 2-exchange neighborhood, in which two elements are exchanged.

        The neighborhood is searched in a randomized ordering.
        Note that frequently, a more problem-specific neighborhood search with delta-evaluation is
        much more efficient!

        :param best_improvement:  if set, the neighborhood is completely searched and a best neighbor is kept;
            otherwise the search terminates in a first-improvement manner, i.e., keeping a first encountered
            better solution.

        :return: True if an improved solution has been found
        """
        n = self.inst.n
        best_obj = orig_obj = self.obj()
        best_p1 = None
        best_p2 = None
        order = np.arange(n)
        np.random.shuffle(order)
        for idx, p1 in enumerate(order[:n-1]):
            for p2 in order[idx+1:]:
                self.x[p1], self.x[p2] = self.x[p2], self.x[p1]
                if self.two_exchange_delta_eval(p1, p2):
                    if self.is_better_obj(self.obj(), best_obj):
                        if not best_improvement:
                            return True
                        best_obj = self.obj()
                        best_p1 = p1
                        best_p2 = p2
                    self.x[p1], self.x[p2] = self.x[p2], self.x[p1]
                    self.obj_val = orig_obj
                    assert self.two_exchange_delta_eval(p1, p2, False)
        if best_p1:
            self.x[best_p1], self.x[best_p2] = self.x[best_p2], self.x[best_p1]
            self.obj_val = best_obj
            return True
        self.obj_val = orig_obj
        return False

    def two_exchange_delta_eval(self, p1: int, p2: int, update_obj_val=True, allow_infeasible=False) -> bool:
        """A 2-exchange move was performed, if feasible update other solution data accordingly, else revert.

        It can be assumed that the solution was in a correct state with a valid objective value before the move.
        The default implementation just calls invalidate() and returns True.

        :param p1: first position
        :param p2: second position
        :param update_obj_val: if set, the objective value should also be updated or invalidate needs to be called
        :param allow_infeasible: if set and the solution is infeasible, the move is nevertheless accepted and
            the update of other data done
        """
        if update_obj_val:
            self.invalidate()
        return True


def cycle_crossover(parent_a: PermutationSolution, parent_b: PermutationSolution):
    posa = {}
    for i in range(0, len(parent_a.x)):
        posa[parent_a.x[i]] = i

    # Detect cycles
    group = np.full(len(parent_a.x), -1)

    group_id = 0
    for i in range(0, len(parent_a.x)):
        if group[i] != -1:
            # Position already in a cycle
            continue

        # Create a new cycle
        pos = i
        while group[pos] == -1:
            # Element at pos i is not yet assigned to a group
            group[pos] = group_id
            sym = parent_b.x[pos]
            pos = posa[sym]

        # sanity check
        assert pos == i
        group_id += 1

    # Perform exchange
    for pos in range(0, len(parent_a.x)):
        if group[pos] % 2 == 0:
            continue

        parent_a.x[pos], parent_b.x[pos] = parent_b.x[pos], parent_a.x[pos]

    return parent_a, parent_b

def partial_matched_crossover(parent_a: PermutationSolution, parent_b: PermutationSolution, swath):
    """A partial-matched-crossover (PMX) exchange.

    Generates the child individual generated from the first parent crossed with the second one

    :param parent_a: first parent
    :param parent_b: second parent
    :param swath: fixed range for exchange
    """

    x = parent_a.x
    y = parent_b.x

    posy = {} # holds the position of every value in solution y
    for i in range(0, len(x)):
        posy[y[i]] = i

    # element with value v in parent x is at position posxy[v] in y
    posxy = {}
    for i in range(0, len(x)):
        posxy[x[i]] = posy[x[i]]

    childx = y.copy()

    done = []

    for i in swath:
        # transfer from fixed range to child
        childx[i] = x[i]

        # begin position calculation
        val = y[i]
        pos = posxy[x[i]]

        if pos == i or i in done:
            continue

        done.append(pos)

        while pos in swath:
            pos = posxy[x[pos]]
            done.append(pos)

        # move val to position
        childx[pos] = val

    parent_a.x = childx

    return parent_a
