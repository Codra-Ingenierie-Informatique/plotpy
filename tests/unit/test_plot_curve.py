# -*- coding: utf-8 -*-
#
# Copyright © 2018 CEA
# Licensed under the terms of the CECILL License
# (see plotpy/__init__.py for details)

"""PlotDialog test"""

import numpy as np

from plotpy.gui.widgets.baseplot import PlotType
from plotpy.gui.widgets.builder import make
from plotpy.gui.widgets.ext_gui_lib import Qt, QwtPlotItem
from plotpy.gui.widgets.plot import BasePlotWidget, PlotDialog
from plotpy.gui.widgets.tools import AntiAliasingTool, AxisScaleTool, CurveStatsTool


def test_plot_curve(qtbot):
    """Test plotting of a curve with PlotDialog"""

    x = np.linspace(-10, 10, 200)
    y = np.sin(x)
    curve = make.curve(x, y, color="g", curvestyle="Sticks")
    curve.setTitle("Curve")

    win = PlotDialog(toolbar=True, options={"type": PlotType.CURVE})
    plot = win.get_plot()
    plot.add_item(curve)

    qtbot.addWidget(win)
    win.show()

    assert isinstance(win.plot_widget, BasePlotWidget)
    assert win.plot_widget.plot == plot

    # Check that specific curve tools are added
    for curve_tool_class in (CurveStatsTool, AntiAliasingTool, AxisScaleTool):
        tool = win.get_tool(curve_tool_class)
        assert tool is not None, f"Tool of type {curve_tool_class} not found"

    qtbot.keyClick(win, Qt.Key_Enter)


def test_plot_curve_anti_aliasing(qtbot):
    """Test Anti-aliasing tool"""

    x = np.linspace(-10, 10, 200)
    y = np.sin(x)
    curve = make.curve(x, y, color="g")

    win = PlotDialog(toolbar=True, options={"type": PlotType.CURVE})
    plot = win.get_plot()
    plot.add_item(curve)

    qtbot.addWidget(win)
    win.show()

    assert isinstance(win.plot_widget, BasePlotWidget)
    assert win.plot_widget.plot == plot

    anti_aliasing_tool = win.get_tool(AntiAliasingTool)
    assert anti_aliasing_tool is not None, "AntiAliasingTool not found"

    original_img = plot.grab().toImage()

    # Activate anti aliasing
    anti_aliasing_tool.activate(True)
    assert plot.antialiased
    assert curve.testRenderHint(QwtPlotItem.RenderAntialiased)
    antialiased_img = plot.grab().toImage()
    assert antialiased_img != original_img

    # Deactivate anti aliasing
    anti_aliasing_tool.activate(False)
    assert not plot.antialiased
    assert not curve.testRenderHint(QwtPlotItem.RenderAntialiased)
    aliased_img = plot.grab().toImage()
    assert original_img == aliased_img

    qtbot.keyClick(win, Qt.Key_Enter)
