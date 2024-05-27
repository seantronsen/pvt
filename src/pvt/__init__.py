# SPDX-FileCopyrightText: 2023-present Sean Tronsen <sean.tronsen@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0

from pvt.apps import *
from pvt.state import *
from pvt.widgets import *
from pvt.panels import *
from pvt.animation import * 
import pyqtgraph as pg

pg.setConfigOption('imageAxisOrder', 'row-major')  # best performance


def run_pyqtgraph_examples():
    """
    A pre-defined function which exists only to save an import call and a
    little typing.
    """
    import pyqtgraph.examples

    pyqtgraph.examples.run()  # pyright: ignore
