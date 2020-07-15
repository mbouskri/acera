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

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMessageBox, QAbstractItemView
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import askdirectory
import ntpath
from torch import load as tload
from torch import no_grad
import csv
import numpy as np
from brain import DiscreteActor
import os
import random
import copy
from envclass import Envir
import time
from urllib.request import urlopen
import requests
import win32api
from functools import partial


global STOP
global RUNNING
global LOADED
global ALIGNED
global TIME
global __version__
STOP = 0
RUNNING = 0
LOADED = 0
ALIGNED = 0
TIME = 0
__version__ = 1.0


def make_ids_seqs(seqs_file):
    ids = []
    seqList = []
    width = 0
    currentSeq = ""
    for line in seqs_file:
        if line[0] == ">":
            ids.append(line[1:].strip())
            if currentSeq != "":
                seqList.append(currentSeq)
            currentSeq = ""
        else:
            currentSeq += line.strip()
    seqList.append(currentSeq)
    for i in range(len(seqList)):
        if len(seqList[i]) > width:
            width = len(seqList[i])
    return width + 1, ids, seqList


def tonp(env):
    nuc = {"A": 1, "T": 2, "C": 3, "G": 4, "-": 5, "*": 6}
    env_int = []
    for i in range(len(env)):
        env_int.append([])
        for j in range(len(env[i])):
            env_int[i].append(nuc[env[i][j]])
    env_numpy = np.array([np.array(xi) for xi in env_int])
    return env_numpy


def todelet(env_numpy):
    mean = np.all(env_numpy == env_numpy[0, :], axis=0)
    todelet = []
    for i in range(len(mean)):
        if mean[i] == True and (env_numpy[0][i] == 6 or env_numpy[0][i] == 5):
            todelet.append(i)
    env_numpy = np.delete(env_numpy, todelet, axis=1)
    return env_numpy


def tonuc(env_numpy):
    env_nuc = []
    re_nuc = {1: "A", 2: "T", 3: "C", 4: "G", 5: "-", 6: "*"}
    for i in range(len(env_numpy)):
        env_nuc.append([])
        for j in range(len(env_numpy[i])):
            env_nuc[i].append(re_nuc[env_numpy[i][j]])
    return env_nuc


def tomatch(env_numpy):
    EM = []
    EMCount = 0
    mean = np.all(env_numpy == env_numpy[0, :], axis=0)
    for i in range(len(mean)):
        if mean[i] == True:
            EM.append("•")
            EMCount += 1
        else:
            EM.append(" ")
    return EM, EMCount


class Ui_aceragui(object):
    def Load(self):
        global RUNNING
        global STOP
        global LOADED
        global ALIGNED

        if RUNNING == 1:
            self.question.setInformativeText("Would you like to stop it?")
            Cond = self.question.exec_()
            if Cond == QMessageBox.Yes:
                STOP = 1
                RUNNING = 0
        if RUNNING == 0:
            ALIGNED = 0
            LOADED = 1
            self.statusbar.showMessage("Loading sequences...")
            global width
            global ids1
            global sequences
            global file_path
            blabla = Tk()
            blabla.withdraw()
            file_path = askopenfilename(parent=blabla)

            def path_tail(path):
                head, tail = ntpath.split(path)
                return tail or ntpath.basename(head)

            if file_path != "":
                extension = path_tail(file_path).split(".")[1]
                if extension == "fasta":
                    seqs_file = open(file_path, "r")
                    width, ids1, sequences = make_ids_seqs(seqs_file)
                    if width > 101 or len(ids1) > 3:
                        self.error.setInformativeText(
                            "The selected sequences exceed model limits \n (Max"
                            " sequences = 3 , Max length = 100)."
                        )
                        self.error.exec_()
                        self.statusbar.showMessage(
                            "The selected sequences exceed model limits (Max sequences"
                            " = 3 , Max length = 100)."
                        )
                    else:
                        self.label.setText(file_path)
                        IDS = QtGui.QStandardItemModel()

                        global maxid
                        maxid = 0

                        for i in range(len(ids1)):
                            if maxid < len(ids1[i]):
                                maxid = len(ids1[i])
                            item = QtGui.QStandardItem(ids1[i])
                            item.setTextAlignment(QtCore.Qt.AlignRight)
                            IDS.appendRow(item)

                        self.listView.setModel(IDS)
                        SEQ = QtGui.QStandardItemModel()
                        for i in range(len(sequences)):
                            SEQ.appendRow(QtGui.QStandardItem(sequences[i]))
                        self.listView_2.setModel(SEQ)

                        ENV = Envir(width, sequences)
                        ENV.reset()
                        score = ENV.reward(False)

                        env = ENV.env
                        env_numpy = tonp(env)
                        env_del_np = todelet(env_numpy)
                        EM, EMCount = tomatch(env_del_np)
                        CSS = QtGui.QStandardItemModel()
                        CSS.appendRow(QtGui.QStandardItem("".join(EM)))

                        self.listView_3.setModel(CSS)
                        self.Scorelabel.setText(
                            "Alignment score:"
                            + str(" ")
                            + str(score)
                            + "\n"
                            + "Exact match: "
                            + str(EMCount)
                        )

                        self.statusbar.showMessage("Sequences loaded")
                        self.progressBar.setProperty("value", 0)
                elif extension != "fasta":
                    self.error.setInformativeText(
                        "Unsupported file extension. Please choose a fasta file."
                    )
                    self.error.exec_()
                    self.statusbar.showMessage("Ready")
            else:
                self.statusbar.showMessage("Ready")

    def Alignthis(self, width, sequences):
        global STOP
        global TIME

        choice = [0, 1, 2]
        RANDOM = 15

        envx = Envir(width, sequences)
        envx.reset()
        MAX = envx.reward(False)

        actor = tload("model/best20mActor0420.pt")
        actor.eval()

        start = time.time()

        for e in range(1500):

            if STOP == 1:
                break

            progress = (e / 1500) * 100
            self.progressBar.setProperty("value", progress)
            QApplication.processEvents()

            env = copy.deepcopy(envx)

            with no_grad():
                broken = False
                for i in range(len(env.env)):
                    if broken == True:
                        break
                    for j in range(len(env.env[i])):
                        position = (i, j)
                        if random.randint(0, 100) < RANDOM:
                            action = random.choice(choice)
                            env.env, reward, done = env.step(position, action)
                        else:
                            state = env.get_state(position)
                            action_probabilities = actor(state)
                            action = action_probabilities.multinomial(1)
                            action = action.data
                            env.env, reward, done = env.step(
                                position, action.numpy()[0][0]
                            )
                        if MAX < reward:
                            MAX = reward
                            envx = copy.deepcopy(env)
                            broken = True
                            break

        end = time.time()
        TIME = end - start
        return envx

    def Align(self):
        global LOADED
        global ALIGNED
        global RUNNING
        global TIME
        global EM
        global STOP

        if LOADED == 0:
            self.error.setInformativeText("Load sequences first.")
            self.error.exec_()
        else:
            STOP = 0
            RUNNING = 1
            self.statusbar.showMessage("Aligning...")
            THIS = self.Alignthis(width, sequences)
            if STOP == 0:
                global Alignment
                Alignment = []
                for i in range(len(THIS.env)):
                    for j in range(len(THIS.env[i])):
                        if THIS.env[i][j] == "*":
                            THIS.env[i][j] = "-"
                env = THIS.env
                env_numpy = tonp(env)
                env_del = todelet(env_numpy)
                env_nuc = tonuc(env_del)

                for i in range(len(env_nuc)):
                    Alignment.append("".join(env_nuc[i]))
                AL = QtGui.QStandardItemModel()
                for i in range(len(Alignment)):
                    AL.appendRow(QtGui.QStandardItem(Alignment[i]))
                self.listView_2.setModel(AL)

                env_del_np = tonp(env_nuc)
                EM, EMCount = tomatch(env_del_np)
                CSS = QtGui.QStandardItemModel()
                CSS.appendRow(QtGui.QStandardItem("".join(EM)))
                self.listView_3.setModel(CSS)

                score = THIS.reward(False)
                self.Scorelabel.setText(
                    "Alignment score:"
                    + str(" ")
                    + str(score)
                    + "\n"
                    + "Exact match: "
                    + str(EMCount)
                )

                ALIGNED = 1
                RUNNING = 0

                status = "Sequences aligned in " + str(round(TIME)) + " seconds."
                self.statusbar.showMessage(status)

    def stop(self):
        global RUNNING
        global STOP

        if RUNNING == 1:
            self.question.setInformativeText("Would you like to stop it?")
            Cond = self.question.exec_()
            if Cond == QMessageBox.Yes:
                STOP = 1
                RUNNING = 0
                self.statusbar.showMessage("Alignment stopped.")
                self.progressBar.setProperty("value", 0)
        else:
            self.error.setInformativeText("No alignment to stop.")
            self.error.exec_()

    def Save(self):
        global ALIGNED
        if ALIGNED == 0:
            self.error.setInformativeText("No alignment to save.")
            self.error.exec_()
        else:
            blabla = Tk()
            blabla.withdraw()
            output_dir = askdirectory()
            if output_dir != "":

                def path_tail(path):
                    head, tail = ntpath.split(path)
                    return tail or ntpath.basename(head)

                o_file = path_tail(file_path).split(".")
                tosave = "Aligned with acera v" + str(__version__) + ".\n" + "\n" + "\n"
                for i in range(len(ids1)):
                    tosave += ids1[i].ljust(maxid + 6, " ") + Alignment[i] + "\n"
                CSSTR = "".join(EM)
                tosave += "".ljust(maxid + 6, " ") + CSSTR
                with open(
                    output_dir + "/" + o_file[0] + " - acera" + ".aln", "w"
                ) as text_file:
                    text_file.write(tosave)
                self.statusbar.showMessage(
                    "Alignment saved to:"
                    + str(" ")
                    + output_dir
                    + "/"
                    + o_file[0]
                    + " - acera"
                    + ".aln"
                )

    def Exit(self):
        sys.exit(app.exec_())

    def About(self):
        self.splash = QSplashScreen(QtGui.QPixmap("images/acera_about.png"))
        self.splash.show()

    def Docum(self):
        os.startfile("User_Guide\\acera_UserGuide.pdf")

    def CheckUpdate(self):
        self.statusbar.showMessage("Checking for updates...")
        QApplication.processEvents()
        try:
            version = urlopen(
                "https://github.com/mbouskri/acera/blob/master/installer/version.txt?raw=true"
            ).read()
            if float(version) > float(__version__):
                self.statusbar.showMessage("Downloading")
                url = (
                    "https://www.dropbox.com/s/1opunosym7v4kj3/acera-installer.exe?dl=1"
                )
                with open("installer/acera-installer.exe", "wb") as f:
                    self.statusbar.showMessage("Downloading updates " + str(0) + "%")
                    QApplication.processEvents()
                    response = requests.get(url, stream=True)
                    total_length = response.headers.get("content-length")
                    if total_length is None:
                        f.write(response.content)
                    else:
                        dl = 0
                        for data in response.iter_content(1024):
                            dl += len(data)
                            f.write(data)
                            done = int(100 * dl / int(total_length))
                            self.statusbar.showMessage(
                                "Downloading updates " + str(done) + "%"
                            )
                            QApplication.processEvents()
                self.statusbar.showMessage("Update downloaded")
                self.update.setInformativeText(
                    "acera will close to install the updates."
                )
                self.update.exec_()
                win32api.ShellExecute(
                    0, "open", "installer\\acera-installer.exe", None, None, 10
                )
                sys.exit(app.exec_())
            else:
                self.statusbar.showMessage("The latest version is installed.")
        except Exception as e:
            self.statusbar.showMessage("Error: No internet connection.")

    def move_scrollbar(self, vs, value):
        vs.blockSignals(True)
        QApplication.processEvents()
        vs.setValue(value)
        QApplication.processEvents()
        vs.blockSignals(False)
        QApplication.processEvents()

    def setupUi(self, aceragui):
        aceragui.setWindowTitle("acera")
        aceragui.setObjectName("acera")
        aceragui.resize(1080, 720)
        aceragui.setMinimumSize(QtCore.QSize(1080, 720))
        aceragui.setMaximumSize(QtCore.QSize(1080, 720))
        aceragui.setWindowOpacity(1.0)
        aceragui.setWindowIcon(QtGui.QIcon("images/ACERAICON.ico"))

        self.centralwidget = QtWidgets.QWidget(aceragui)
        self.centralwidget.setObjectName("centralwidget")
        self.LoadBox = QtWidgets.QGroupBox(self.centralwidget)
        self.LoadBox.setEnabled(True)
        self.LoadBox.setGeometry(QtCore.QRect(10, 20, 501, 80))
        self.LoadBox.setFlat(False)
        self.LoadBox.setCheckable(False)
        self.LoadBox.setObjectName("LoadBox")
        self.label = QtWidgets.QLabel(self.LoadBox)
        self.label.setGeometry(QtCore.QRect(10, 30, 361, 31))
        self.label.setFrameShape(QtWidgets.QFrame.WinPanel)
        self.label.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.label.setText("")
        self.label.setObjectName("label")

        self.LoadB = QtWidgets.QPushButton(self.LoadBox)
        self.LoadB.setGeometry(QtCore.QRect(390, 30, 93, 28))
        self.LoadB.setObjectName("LoadB")
        self.LoadB.clicked.connect(self.Load)

        self.error = QMessageBox()
        self.error.setIcon(QMessageBox.Critical)
        self.error.setText("Error")
        self.error.setWindowTitle("acera")
        self.error.setWindowIcon(QtGui.QIcon("images/ACERAICON.png"))

        self.update = QMessageBox()
        self.update.setIcon(QMessageBox.Warning)
        self.update.setText("Update")
        self.update.setWindowTitle("acera")
        self.update.setWindowIcon(QtGui.QIcon("images/ACERAICON.png"))

        self.question = QMessageBox()
        self.question.setIcon(QMessageBox.Warning)
        self.question.setText("An alignment is running")
        self.question.setWindowTitle("acera")
        self.question.setWindowIcon(QtGui.QIcon("images/ACERAICON.png"))
        self.question.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        self.groupBox_2 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_2.setGeometry(QtCore.QRect(560, 20, 501, 80))
        self.groupBox_2.setObjectName("groupBox_2")
        self.splitter = QtWidgets.QSplitter(self.groupBox_2)
        self.splitter.setGeometry(QtCore.QRect(80, 30, 365, 28))
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.AlignB = QtWidgets.QPushButton(self.splitter)
        self.AlignB.setObjectName("AlignB")
        self.AlignB.clicked.connect(self.Align)
        self.StopB = QtWidgets.QPushButton(self.splitter)
        self.StopB.setObjectName("StopB")
        self.StopB.clicked.connect(self.stop)
        self.SaveB = QtWidgets.QPushButton(self.splitter)
        self.SaveB.setObjectName("SaveB")
        self.SaveB.clicked.connect(self.Save)

        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setGeometry(QtCore.QRect(10, 640, 1051, 23))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setObjectName("progressBar")

        font = QtGui.QFont()
        font.setFamily("Consolas")
        font.setPointSize(10)

        self.IDBOX = QtWidgets.QGroupBox(self.centralwidget)
        self.IDBOX.setGeometry(QtCore.QRect(10, 120, 281, 431))
        self.IDBOX.setObjectName("IDBOX")
        self.listView = QtWidgets.QListView(self.IDBOX)
        self.listView.setGeometry(QtCore.QRect(10, 20, 256, 401))
        self.listView.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.listView.setObjectName("listView")
        self.listView.setFont(font)
        self.listView.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.SeqBOX = QtWidgets.QGroupBox(self.centralwidget)
        self.SeqBOX.setGeometry(QtCore.QRect(300, 120, 761, 431))
        self.SeqBOX.setObjectName("SeqBOX")
        self.listView_2 = QtWidgets.QListView(self.SeqBOX)
        self.listView_2.setGeometry(QtCore.QRect(10, 20, 741, 401))
        self.listView_2.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.listView_2.setObjectName("listView_2")
        self.listView_2.setFont(font)
        self.listView_2.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.vs1 = self.listView_2.horizontalScrollBar()

        self.ScoreBOX = QtWidgets.QGroupBox(self.centralwidget)
        self.ScoreBOX.setGeometry(QtCore.QRect(10, 550, 281, 80))
        self.ScoreBOX.setObjectName("ScoreBOX")
        self.Scorelabel = QtWidgets.QLabel(self.ScoreBOX)
        self.Scorelabel.setGeometry(QtCore.QRect(10, 25, 261, 41))
        self.Scorelabel.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.Scorelabel.setFrameShadow(QtWidgets.QFrame.Plain)
        self.Scorelabel.setText("")
        self.Scorelabel.setObjectName("Scorelabel")

        self.listView_3 = QtWidgets.QListView(self.centralwidget)
        self.listView_3.setGeometry(QtCore.QRect(310, 560, 741, 71))
        self.listView_3.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.listView_3.setObjectName("listView_3")
        self.listView_3.setFont(font)
        self.listView_3.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.vs2 = self.listView_3.horizontalScrollBar()

        self.vs1.valueChanged.connect(partial(self.move_scrollbar, self.vs2))
        self.vs2.valueChanged.connect(partial(self.move_scrollbar, self.vs1))

        aceragui.setCentralWidget(self.centralwidget)

        self.menubar = QtWidgets.QMenuBar(aceragui)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1080, 26))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuAlignement = QtWidgets.QMenu(self.menubar)
        self.menuAlignement.setObjectName("menuAlignement")
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        aceragui.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(aceragui)
        self.statusbar.setObjectName("statusbar")
        aceragui.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready.")

        self.actionLoad_sequences = QtWidgets.QAction(aceragui)
        self.actionLoad_sequences.setObjectName("actionLoad_sequences")
        self.actionLoad_sequences.triggered.connect(self.Load)

        self.actionSave_alignment = QtWidgets.QAction(aceragui)
        self.actionSave_alignment.setObjectName("actionSave_alignment")
        self.actionSave_alignment.triggered.connect(self.Save)

        self.actionExit = QtWidgets.QAction(aceragui)
        self.actionExit.setObjectName("actionExit")
        self.actionExit.triggered.connect(self.Exit)

        self.actionAlign_sequences = QtWidgets.QAction(aceragui)
        self.actionAlign_sequences.setObjectName("actionAlign_sequences")
        self.actionAlign_sequences.triggered.connect(self.Align)

        self.actionStop_alignment = QtWidgets.QAction(aceragui)
        self.actionStop_alignment.setObjectName("actionStop_alignment")
        self.actionStop_alignment.triggered.connect(self.stop)

        self.actionDocumentation = QtWidgets.QAction(aceragui)
        self.actionDocumentation.setObjectName("actionDocumentation")
        self.actionDocumentation.triggered.connect(self.Docum)

        self.actionCheckUpdate = QtWidgets.QAction(aceragui)
        self.actionCheckUpdate.setObjectName("actionCheckUpdate")
        self.actionCheckUpdate.triggered.connect(self.CheckUpdate)

        self.actionAbout = QtWidgets.QAction(aceragui)
        self.actionAbout.setObjectName("actionAbout")
        self.actionAbout.triggered.connect(self.About)

        self.menuFile.addAction(self.actionLoad_sequences)
        self.menuFile.addAction(self.actionSave_alignment)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuAlignement.addAction(self.actionAlign_sequences)
        self.menuAlignement.addAction(self.actionStop_alignment)
        self.menuHelp.addSeparator()
        self.menuHelp.addAction(self.actionDocumentation)
        self.menuHelp.addAction(self.actionCheckUpdate)
        self.menuHelp.addSeparator()
        self.menuHelp.addAction(self.actionAbout)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuAlignement.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(aceragui)
        QtCore.QMetaObject.connectSlotsByName(aceragui)

    def retranslateUi(self, aceragui):
        _translate = QtCore.QCoreApplication.translate
        aceragui.setWindowTitle(_translate("aceragui", "acera v" + str(__version__)))
        self.LoadBox.setTitle(_translate("aceragui", "Load sequences:"))
        self.LoadB.setText(_translate("aceragui", "Load"))
        self.groupBox_2.setTitle(_translate("aceragui", "Alignment:"))
        self.AlignB.setText(_translate("aceragui", "Align"))
        self.StopB.setText(_translate("aceragui", "Stop alignment"))
        self.SaveB.setText(_translate("aceragui", "Save alignment"))
        self.IDBOX.setTitle(_translate("aceragui", "Sequences ID:"))
        self.SeqBOX.setTitle(_translate("aceragui", "Sequences:"))
        self.ScoreBOX.setTitle(_translate("aceragui", "Score:"))
        self.menuFile.setTitle(_translate("aceragui", "File"))
        self.menuAlignement.setTitle(_translate("aceragui", "Alignment"))
        self.menuHelp.setTitle(_translate("aceragui", "Help"))
        self.actionLoad_sequences.setText(_translate("aceragui", "Load sequences"))
        self.actionSave_alignment.setText(_translate("aceragui", "Save alignment"))
        self.actionExit.setText(_translate("aceragui", "Exit"))
        self.actionAlign_sequences.setText(_translate("aceragui", "Align sequences"))
        self.actionStop_alignment.setText(_translate("aceragui", "Stop alignment"))
        self.actionDocumentation.setText(_translate("aceragui", "User Guide"))
        self.actionAbout.setText(_translate("aceragui", "About"))
        self.actionCheckUpdate.setText(_translate("aceragui", "Check for updates"))


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    splash = QSplashScreen(QtGui.QPixmap("images/acerasplashshadow.png"))
    statusbar = QtWidgets.QLabel(splash)
    pal = statusbar.palette()
    pal.setColor(QtGui.QPalette.WindowText, QtGui.QColor("lightgrey"))
    statusbar.setPalette(pal)
    statusbar.setGeometry(15, 453, 8 * splash.width() / 10, splash.height() / 10)
    statusbar.setText("Checking for updates...")
    splash.show()
    time.sleep(1)
    TRUE = False
    try:
        version = urlopen(
            "https://github.com/mbouskri/acera/blob/master/installer/version.txt?raw=true"
        ).read()
        if float(version) > float(__version__):
            statusbar.setText("Downloading the latest version...")
            app.processEvents()
            url = "https://www.dropbox.com/s/1opunosym7v4kj3/acera-installer.exe?dl=1"
            with open("installer/acera-installer.exe", "wb") as f:
                statusbar.setText("Downloading updates ")
                app.processEvents()
                response = requests.get(url, stream=True)
                total_length = response.headers.get("content-length")
                if total_length is None:
                    f.write(response.content)
                else:
                    dl = 0
                    for data in response.iter_content(1024):
                        dl += len(data)
                        f.write(data)
                        done = int(100 * dl / int(total_length))
                        statusbar.setText("Downloading updates " + str(done) + "%")
                        app.processEvents()

            statusbar.setText("Update downloaded.")
            app.processEvents()
            statusbar.setText("acera will close to install the updates.")
            app.processEvents()
            time.sleep(1.5)
            win32api.ShellExecute(
                0, "open", "installer\\acera-installer.exe", None, None, 10
            )
            splash.close()
            TRUE = True
        else:
            statusbar.setText("The latest version is installed.")
            app.processEvents()
    except Exception as e:
        statusbar.setText("Error: No internet connection.")
        app.processEvents()
    time.sleep(1.5)
    splash.close()
    if TRUE == False:
        aceragui = QtWidgets.QMainWindow()
        ui = Ui_aceragui()
        ui.setupUi(aceragui)
        aceragui.show()
        sys.exit(app.exec_())
