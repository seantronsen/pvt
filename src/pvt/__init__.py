# SPDX-FileCopyrightText: 2023-present Sean Tronsen <sean.tronsen@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0

import pyqtgraph as pg

# todo: consider adding something for cupy at a later date to take advantage of
# GPU computations
# configuration for best performance
pg.setConfigOptions(imageAxisOrder='row-major', useNumba=True)


def run_pyqtgraph_examples():
    """
    A pre-defined function which exists only to save an import call and a
    little typing.
    """
    import pyqtgraph.examples

    pyqtgraph.examples.run()  # pyright: ignore
