# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see plotpy/LICENSE for details)

"""
SelectPointTool test

This plotpy tool provide a MATLAB-like "ginput" feature.
"""

# guitest: show

from guidata.qthelpers import exec_dialog, qt_app_context
from numpy import linspace, sin

from plotpy.builder import make
from plotpy.config import _
from plotpy.tools import EditPointTool


def callback_function(tool: EditPointTool):
    print("New arrays:", tool.get_arrays())
    print("Indexed changes:", tool.get_changes())


def edit_downsampled_curve(downsampling_factor: int, *args):
    """
    Plot curves and return selected point(s) coordinates
    """
    win = make.dialog(
        wintitle=_("Select one point then press OK to accept"),
        edit=True,
        type="curve",
    )
    default = win.manager.add_tool(
        EditPointTool,
        title="Test",
        end_callback=callback_function,
    )
    default.activate()
    plot = win.manager.get_plot()
    for cx, cy in args[:-1]:
        item = make.mcurve(cx, cy)

        plot.add_item(item)
    item = make.mcurve(
        *args[-1], "r-+", downsampling_factor=downsampling_factor, use_downsampling=True
    )
    plot.add_item(item)
    plot.set_active_item(item)
    plot.unselect_item(item)
    exec_dialog(win)
    return args


def test_edit_curve():
    """Test"""
    with qt_app_context(exec_loop=False):
        nlines = 1000
        x = linspace(-10, 10, num=nlines)
        y = 0.25 * sin(sin(sin(x * 0.5)))
        x2 = linspace(-10, 10, num=nlines)
        y2 = sin(sin(sin(x2)))
        edited_args = edit_downsampled_curve(50, (x, y), (x2, y2), (x, sin(2 * y)))
        edit_downsampled_curve(10, *edited_args)


if __name__ == "__main__":
    test_edit_curve()
