# -*- coding: utf-8 -*-
#
# Copyright © 2015 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see plotpy/__init__.py for details)

"""DICOM image test

Requires pydicom (>=0.9.3)"""


import os

from plotpy.widgets.builder import make
from plotpy.widgets.plot.plotwidget import PlotDialog, PlotType
from plotpy.widgets.qthelpers_guidata import qt_app_context

SHOW = True  # Show test in GUI-based test launcher


def test_dicom_image():
    with qt_app_context(exec_loop=True):
        win = PlotDialog(
            edit=False,
            toolbar=True,
            wintitle="DICOM I/O test",
            options=dict(show_contrast=True, type=PlotType.IMAGE),
        )
        filename = os.path.join(os.path.dirname(__file__), "mr-brain.dcm")
        image = make.image(filename=filename, title="DICOM img", colormap="gray")
        plot = win.manager.get_plot()
        plot.add_item(image)
        plot.select_item(image)
        contrast = win.manager.get_contrast_panel()
        contrast.histogram.eliminate_outliers(54.0)
        win.resize(600, 700)


if __name__ == "__main__":
    win = test_dicom_image()
