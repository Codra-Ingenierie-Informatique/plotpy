# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see plotpy/LICENSE for details)

"""Histogram test"""

# guitest: show

from guidata.qthelpers import qt_app_context
from numpy.random import normal

from plotpy.builder import make
from plotpy.constants import PlotType
from plotpy.plot import PlotDialog


def test_histogram():
    """Test"""
    with qt_app_context(exec_loop=True):
        data = normal(0, 1, (2000,))
        win = PlotDialog(
            edit=False,
            toolbar=True,
            wintitle="Histogram test",
            options={"type": PlotType.CURVE},
        )
        plot = win.manager.get_plot()
        plot.add_item(make.histogram(data))
        win.show()


if __name__ == "__main__":
    test_histogram()
