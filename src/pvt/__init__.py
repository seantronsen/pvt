# SPDX-FileCopyrightText: 2023-present Sean Tronsen <sean.tronsen@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0

from qtviewer.apps import *
from qtviewer.state import *
from qtviewer.widgets import *
from qtviewer.panels import *
from qtviewer.animation import * 
import pyqtgraph as pg

pg.setConfigOption('imageAxisOrder', 'row-major')  # best performance


def run_pyqtgraph_examples():
    """
    A pre-defined function which exists only to save an import call and a
    little typing.
    """
    import pyqtgraph.examples

    pyqtgraph.examples.run()  # pyright: ignore
