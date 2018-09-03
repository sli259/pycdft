import numpy as np
from pycdft.common.sample import Sample
from pycdft.common.fragment import Fragment
from pycdft.optimizer import Optimizer
from .base import Constraint


class ChargeConstraint(Constraint):
    """ Constraint on the absolute electron number of a fragment.

    Extra attributes:
        fragment (Fragment): a fragment of the whole system.
    """

    type = "charge"
    _eps = 0.0001  # cutoff of Hirshfeld weight when the density approaches zero

    def __init__(self, sample: Sample, fragment: Fragment, N0, optimizer: Optimizer,
                 V_init=0.0, Ntol=None, Vtol=None, dVtol=1.0E-2):
        super(ChargeConstraint, self).__init__(sample, N0, optimizer, V_init=V_init,
                                               Ntol=Ntol, Vtol=Vtol, dVtol=dVtol)
        self.fragment = fragment

    def update_weight(self):
        self.weight = self.fragment.rhopro_r / self.sample.rhopro_tot_r
        self.weight[self.sample.rhopro_tot_r < self._eps] = 0.0
        self.is_converged = False

    def update_N(self):
        omega = self.sample.omega
        n123 = self.sample.n1 * self.sample.n2 * self.sample.n3
        rho_r = self.sample.rho_r
        self.N = (omega / n123) * np.sum(np.einsum("ijk,sijk->s", self.weight, rho_r))

    def update_Vc(self):
        if self.sample.nspin == 1:
            self.Vc = self.V * self.weight[None, ...]
        else:
            self.Vc = np.append(self.weight, self.weight, axis=0).reshape(2, *self.weight.shape)

    def update_Fc(self):
        omega = self.sample.omega
        n123 = self.sample.n123
        rhor = np.sum(self.sample.rho_r, axis=0)
        self.Fc = np.zeros([self.sample.natoms, 3])

        for iatom, atom in enumerate(self.sample.atoms):
            w_grad = self.fragment.compute_w_grad(atom, self.weight)
            self.Fc[iatom] = (omega * n123) * self.V * np.einsum("ijk,aijk->a", rhor, w_grad)
