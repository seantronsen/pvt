# SPDX-FileCopyrightText: 2023-present Sean Tronsen <sean.tronsen@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0

import pyqtgraph as pg
from qtviewer.apps import *
from qtviewer.state import *
from qtviewer.widgets import *
from qtviewer.panels import *

pg.setConfigOption('imageAxisOrder', 'row-major')  # best performance


def run_pyqtgraph_examples():
    import pyqtgraph.examples
    pyqtgraph.examples.run()  # pyright: ignore
