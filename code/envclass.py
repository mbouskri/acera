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

import copy
from torch import FloatTensor
import numpy as np
import random


class Envir():
    def __init__(self, width, sequences):

        self.width = width
        self.sequences = sequences
        self.envr = self.make()
        self.env = self.make()

    def make(self):
        Matrix = [['*' for i in range(self.width)]
                  for j in range(len(self.sequences))]
        for i in range(len(self.sequences)):
            for j in range(len(self.sequences[i])):
                Matrix[i][j] = self.sequences[i][j]
        return Matrix

    def mutate(self, p):
        nucs = ["A", "C", "T", "G"]
        for i in range(len(self.env)):
            if random.randint(0, 100) < p:
                j = random.randint(0, self.width - 1)
                self.env[i][j] = random.choice(nucs)

    def reset(self):
        self.env = copy.deepcopy(self.envr)

    def get_state(self, position):
        i = position[0]
        j = position[1]
        nuc = {"A": 1, "T": 2, "C": 3, "G": 4, "-": 5, "*": 6}
        state = []
        if i != len(self.env) - 1:
            if j < len(self.env[i]) - 1:
                if j == 0:
                    state = [nuc[self.env[i][j]], nuc[self.env[i][j + 1]], nuc[self.env[i][j + 2]],
                             nuc[self.env[i + 1][j]], nuc[self.env[i + 1][j + 1]], nuc[self.env[i + 1][j + 2]]]
                    this = self.reward(False)
                    state.append(this)
                    state = FloatTensor(np.reshape(state, [1, 7]))
                else:
                    state = [nuc[self.env[i][j - 1]], nuc[self.env[i][j]], nuc[self.env[i][j + 1]],
                             nuc[self.env[i + 1][j - 1]], nuc[self.env[i + 1][j]], nuc[self.env[i + 1][j + 1]]]
                    this = self.reward(False)
                    state.append(this)
                    state = FloatTensor(np.reshape(state, [1, 7]))
            else:
                state = [nuc[self.env[i][j - 2]], nuc[self.env[i][j - 1]], nuc[self.env[i][j]],
                         nuc[self.env[i + 1][j - 2]], nuc[self.env[i + 1][j - 1]], nuc[self.env[i + 1][j]]]
                this = self.reward(False)
                state.append(this)
                state = FloatTensor(np.reshape(state, [1, 7]))
        elif i == len(self.env) - 1:
            if j < len(self.env[i]) - 1:
                if j == 0:
                    state = [nuc[self.env[i][j]], nuc[self.env[i][j + 1]], nuc[self.env[i][j + 2]],
                             nuc[self.env[i - 1][j]], nuc[self.env[i - 1][j + 1]], nuc[self.env[i - 1][j + 2]]]
                    this = self.reward(False)
                    state.append(this)
                    state = FloatTensor(np.reshape(state, [1, 7]))
                else:
                    state = [nuc[self.env[i][j - 1]], nuc[self.env[i][j]], nuc[self.env[i][j + 1]],
                             nuc[self.env[i - 1][j - 1]], nuc[self.env[i - 1][j]], nuc[self.env[i - 1][j + 1]]]
                    this = self.reward(False)
                    state.append(this)
                    state = FloatTensor(np.reshape(state, [1, 7]))
            else:
                state = [nuc[self.env[i][j - 2]], nuc[self.env[i][j - 1]], nuc[self.env[i][j]],
                         nuc[self.env[i - 1][j - 2]], nuc[self.env[i - 1][j - 1]], nuc[self.env[i - 1][j]]]
                this = self.reward(False)
                state.append(this)
                state = FloatTensor(np.reshape(state, [1, 7]))

        return state

    def get_state_reward(self, position):
        i = position[0]
        j = position[1]
        state_reward = 0
        if i != len(self.env) - 1:
            if j < len(self.env) - 1:
                state = [self.env[i][j], self.env[i][j + 1],
                         self.env[i + 1][j], self.env[i + 1][j + 1]]
                state_reward = self.SOP(state[0:1], state[2:3])
            else:
                state = [self.env[i][j], self.env[i][j - 1],
                         self.env[i + 1][j], self.env[i + 1][j - 1]]
                state_reward = self.SOP(state[0:1], state[2:3])
        elif i == len(self.env) - 1:
            if j < len(self.env) - 1:
                state = [self.env[i][j], self.env[i][j + 1],
                         self.env[i - 1][j], self.env[i - 1][j + 1]]
                state_reward = self.SOP(state[0:1], state[2:3])
            else:
                state = [self.env[i][j], self.env[i][j - 1],
                         self.env[i - 1][j], self.env[i - 1][j - 1]]
                state_reward = self.SOP(state[0:1], state[2:3])

        return state_reward

    def step(self, position, action):
        done = False
        r = position[0]
        c = position[1]
        gapmove = False
        if action == 0:
            if self.check_action(self.env, position) == False:
                return self.env, self.reward(gapmove), done
            else:
                gapmove = False
                temp1 = self.env[r][c]
                self.env[r][c] = '-'
                for j in range(c, 0, -1):
                    if self.env[r][j - 1] != '-' and self.env[r][j - 1] != '*':
                        temp2 = self.env[r][j - 1]
                        self.env[r][j - 1] = temp1
                        temp1 = temp2
                    else:
                        self.env[r][j - 1] = temp1
                        break
                return self.env, self.reward(gapmove), done
        elif action == 1:
            gapmove = False
            temp1 = self.env[r][c]
            self.env[r][c] = '-'
            if c == len(self.env[r]) - 1:
                for k in range(len(self.env)):
                    self.env[k].append('*')
            for j in range(c, len(self.env[r]) - 1):
                if j + 1 == len(self.env[r]) - 1:
                    for k in range(len(self.env)):
                        self.env[k].append('*')
                if self.env[r][j + 1] != '-' and self.env[r][j + 1] != '*':
                    temp2 = self.env[r][j + 1]
                    self.env[r][j + 1] = temp1
                    temp1 = temp2
                elif self.env[r][j + 1] == '-' or self.env[r][j + 1] == '*':
                    self.env[r][j + 1] = temp1
                    break
            return self.env, self.reward(gapmove), done

        elif action == 2:
            gapmove = False
            return self.env, self.reward(gapmove), done

    @staticmethod
    def check_action(env, position):
        if position[1] == 0:
            return False
        else:
            search_set = set(env[position[0]][0:position[1]])
            for char in search_set:
                if char == '-':
                    return True
            return False

    def reward(self, gapmove):
        if gapmove:
            return -999
        else:
            return self.alignmentscore()

    def alignmentscore(self):
        alsc = 0
        for i in range(len(self.env) - 1):
            for j in range(i + 1, len(self.env)):
                alsc = alsc + self.SOP(self.env[i], self.env[j])
        return alsc

    @staticmethod
    def SOP(s1, s2):
        sop = 0
        for i in range(len(s1)):
            if s1[i] == s2[i] and s1[i] != '-' and s1[i] != '*' and s2[i] != '-' and s2[i] != '*':
                sop = sop + 2
            elif s1[i] != s2[i] and s1[i] != '-' and s1[i] != '*' and s2[i] != '-' and s2[i] != '*':
                sop = sop - 1
            elif s1[i] != s2[i] and (((s1[i] != '-' and s1[i] != '*' and (s2[i] == '-' or s2[i] == '*')))
                                     or ((s2[i] != '-' and s2[i] != '*' and (s1[i] == '-' or s1[i] == '*')))):
                sop = sop - 2
            elif s1[i] == s2[i] and (s1[i] == '*' or s1[i] == '-') and (s2[i] == '*' or s2[i] == '-'):
                sop = sop + 0
        return sop
