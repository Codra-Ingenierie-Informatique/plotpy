# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see plotpy/__init__.py for details)

"""Contrast tool test"""


import os.path as osp

from plotpy.widgets.builder import make
from plotpy.widgets.plot.plotwidget import PlotDialog, PlotType
from plotpy.widgets.qthelpers_guidata import qt_app_context

SHOW = True  # Show test in GUI-based test launcher


def test_contrast():
    """Test"""
    # -- Create QApplication
    with qt_app_context(exec_loop=True):
        filename = osp.join(osp.dirname(__file__), "brain.png")
        image = make.image(filename=filename, title="Original", colormap="gray")

        win = PlotDialog(
            edit=False,
            toolbar=True,
            wintitle="Contrast test",
            options=dict(show_contrast=True, type=PlotType.IMAGE),
        )
        plot = win.manager.get_plot()
        plot.add_item(image)
        win.resize(600, 600)
        win.show()
        try:
            plot.save_widget("contrast.png")
        except IOError:
            # Skipping this part of the test
            # because user has no write permission on current directory
            pass


if __name__ == "__main__":
    test_contrast()
