# -*- coding: utf-8 -*-
# This file is part of AYAB.
#
#    AYAB is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    AYAB is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with AYAB.  If not, see <http://www.gnu.org/licenses/>.
#
#    Copyright 2014 Sebastian Oliva, Christian Obersteiner,
#       Andreas Müller, Christian Gerbrandt
#    https://github.com/AllYarnsAreBeautiful/ayab-desktop
"""Provides a graphical interface for users to operate AYAB."""

from __future__ import annotations
import sys
import logging

from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import QCoreApplication


from .main_gui import Ui_MainWindow
from .gui_fsm import gui_fsm
from .signal_receiver import SignalReceiver
from .audio import AudioPlayer
from .menu import Menu
from .scene import Scene
from .transforms import Transform
from .firmware_flash import FirmwareFlash
from .hw_test import HardwareTestDialog
from .preferences import Preferences
from . import utils

# from .statusbar import StatusBar
from .progressbar import ProgressBar
from .about import About
from .knitprogress import KnitProgress
from .thread import GenericThread
from .engine import Engine
from .engine.engine_fsm import Operation
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..main import AppContext


class GuiMain(QMainWindow):
    """
    GuiMain is the top level class in the AYAB GUI.

    GuiMain inherits from QMainWindow and instantiates a window with
    components from `menu_gui.ui`.
    """

    def __init__(self, app_context: AppContext):
        super().__init__()
        self.app_context = app_context

        # get preferences
        self.signal_receiver = SignalReceiver()
        self.prefs = Preferences(self)

        # create UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle(f"AYAB {utils.package_version(app_context)}")

        # add modular components
        self.menu = Menu(self)
        self.setMenuBar(self.menu)
        # self.statusbar = StatusBar(self)
        # self.setStatusBar(self.statusbar)
        self.about: About = About(self)
        self.scene: Scene = Scene(self)
        self.engine: Engine = Engine(self)
        self.hw_test = HardwareTestDialog(self)
        self.progbar = ProgressBar(self)
        self.knitprog = KnitProgress(self)
        self.flash = FirmwareFlash(self)
        self.audio = AudioPlayer(self)
        self.knit_thread = GenericThread(self.engine.run, Operation.KNIT)
        self.test_thread = GenericThread(self.engine.run, Operation.TEST)

        # show UI
        self.showMaximized()

        # Activate signals and UI elements
        self.signal_receiver.activate_signals(self)
        self.__activate_ui()
        self.__activate_menu()

        # initialize FSM
        self.fsm = gui_fsm()
        self.fsm.set_transitions(self)
        self.fsm.set_properties(self)
        self.fsm.machine.start()

    def __activate_ui(self) -> None:
        self.ui.open_image_file_button.clicked.connect(self.scene.ayabimage.select_file)
        self.ui.filename_lineedit.returnPressed.connect(
            self.scene.ayabimage.select_file
        )
        self.ui.cancel_button.clicked.connect(self.engine.cancel)
        self.hw_test.finished.connect(lambda: self.finish_operation(Operation.TEST))

    def __activate_menu(self) -> None:
        self.menu.ui.action_open_image_file.triggered.connect(
            self.scene.ayabimage.select_file
        )
        self.menu.ui.action_quit.triggered.connect(self.__quit)
        self.menu.ui.action_load_AYAB_firmware.triggered.connect(self.flash.open)
        self.menu.ui.action_cancel.triggered.connect(self.engine.cancel)
        self.menu.ui.action_set_preferences.triggered.connect(self.__set_prefs)
        self.menu.ui.action_about.triggered.connect(self.about.show)
        # get names of image actions from Transform methods
        transforms = filter(lambda x: x[0] != "_", Transform.__dict__.keys())
        for t in transforms:
            action = getattr(self.menu.ui, "action_" + t)
            slot = getattr(self.scene.ayabimage, t)
            action.triggered.connect(slot)

    def __set_prefs(self) -> None:
        self.prefs.open_dialog()
        self.scene.refresh()
        self.engine.reload_settings()

    def __quit(self) -> None:
        logging.debug("Quitting")
        instance = QCoreApplication.instance()
        if instance is not None:
            instance.quit()
        sys.exit()

    def start_knitting(self) -> None:
        """Start the knitting process."""
        self.start_operation()
        # reset knit progress window
        self.knitprog.start()
        # start thread for knit engine
        self.knit_thread.start()

    def start_testing(self) -> None:
        """Start the testing process."""
        self.start_operation()
        # start thread for test engine
        self.test_thread.start()

    def start_operation(self) -> None:
        """Disable UI elements at start of operation."""
        self.ui.filename_lineedit.setEnabled(False)
        self.ui.open_image_file_button.setEnabled(False)
        self.menu.setEnabled(False)

    def finish_operation(self, operation: Operation) -> None:
        """(Re-)enable UI elements after operation finishes."""
        if operation == Operation.KNIT:
            self.knit_thread.wait()
        else:
            # operation = Operation.TEST:
            self.test_thread.wait()
        self.ui.filename_lineedit.setEnabled(True)
        self.ui.open_image_file_button.setEnabled(True)
        self.menu.setEnabled(True)

    def set_image_dimensions(self) -> None:
        """Set dimensions of image."""
        width, height = self.scene.ayabimage.image.size
        self.engine.config.update_needles()  # in case machine width changed
        self.engine.config.set_image_dimensions(width, height)
        self.progbar.update(self.engine.status)
        self.notify(
            QCoreApplication.translate("Scene", "Image dimensions")
            + f": {width} x {height}",
            False,
        )
        self.scene.refresh()

    def update_start_row(self, start_row: int) -> None:
        self.scene.row_progress = start_row
        self.engine.status.current_row = start_row
        self.progbar.update(self.engine.status)

    def notify(self, text: str, log: bool = True) -> None:
        """Update the notification field."""
        if log:
            logging.info("Notification: " + text)
        self.ui.label_notifications.setText(text)
