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
"""
    Parts of this code are licensed under the MIT License

    Copyright (c) 2017 Didier Chételat

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included
    in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
"""

import numpy as np
import torch.nn
import torch.nn.functional as F
from torch.autograd import Variable

class DiscreteActor(torch.nn.Module):

    def __init__(self):
        super().__init__()

        self.input_layer = torch.nn.Linear(7, 32)
        self.hidden_layer = torch.nn.Linear(32, 32)
        self.hidden_layer2 = torch.nn.Linear(32, 32)
        self.hidden_layer3 = torch.nn.Linear(32, 32)
        self.action_layer = torch.nn.Linear(32, 3)

    def forward(self, states):

        hidden = F.leaky_relu(self.input_layer(states), negative_slope=0.01)
        hidden = F.leaky_relu(self.hidden_layer(hidden), negative_slope=0.01)
        hidden = F.leaky_relu(self.hidden_layer2(hidden), negative_slope=0.01)
        hidden = F.leaky_relu(self.hidden_layer3(hidden), negative_slope=0.01)
        action_probabilities = F.softmax(self.action_layer(hidden), dim=-1)
        return action_probabilities

class Brain:

    def __init__(self):
        self.actor = None

class DiscreteBrain(Brain):
    def __init__(self):
        super().__init__()
        self.actor = DiscreteActor()

brain = DiscreteBrain()
