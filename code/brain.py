"""
    Copyright © 2020 Mehdi Bouskri

    This file is part of acera.

    acera is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    acera is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with acera.  If not, see <https://www.gnu.org/licenses/>.

"""

import numpy as np
import torch.nn
import torch.nn.functional as F
from torch.autograd import Variable


class DiscreteActor(torch.nn.Module):
    """
    Discrete actor network.
    """

    def __init__(self):
        super().__init__()

        self.input_layer = torch.nn.Linear(7, 32)
        self.hidden_layer = torch.nn.Linear(32, 32)
        self.hidden_layer2 = torch.nn.Linear(32, 32)
        self.hidden_layer3 = torch.nn.Linear(32, 32)
        self.action_layer = torch.nn.Linear(32, 3)

    def forward(self, states):
        """
        Compute a forward pass in the network.

        Parameters
        ----------
        states : torch.Tensor
            The states for which the action probabilities must be computed.

        Returns
        -------
        action_probabilities : torch.Tensor
            The action probabilities of the policy according to the actor.
        """

        hidden = F.leaky_relu(self.input_layer(states), negative_slope=0.01)
        hidden = F.leaky_relu(self.hidden_layer(hidden), negative_slope=0.01)
        hidden = F.leaky_relu(self.hidden_layer2(hidden), negative_slope=0.01)
        hidden = F.leaky_relu(self.hidden_layer3(hidden), negative_slope=0.01)
        action_probabilities = F.softmax(self.action_layer(hidden), dim=-1)
        return action_probabilities


class Brain:
    """
    A centralized brain for the agents.
    """

    def __init__(self):
        self.actor = None


class DiscreteBrain(Brain):
    def __init__(self):
        super().__init__()
        self.actor = DiscreteActor()


brain = DiscreteBrain()
