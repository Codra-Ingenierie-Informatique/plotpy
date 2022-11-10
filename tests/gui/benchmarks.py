# -*- coding: utf-8 -*-
#
# Copyright © 2011 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see plotpy/__init__.py for details)

"""plotpy plot benchmarking"""

SHOW = False  # Show test in GUI-based test launcher


import time
import numpy as np

from plotpy.gui.widgets.builder import make
from plotpy.gui.widgets.ext_gui_lib import QApplication
from plotpy.gui.widgets.baseplot import PlotType
from plotpy.gui.widgets.plot import PlotWindow


class BaseBM(object):
    """Benchmark object"""

    MAKE_FUNC = None
    WIN_TYPE = PlotType.AUTO

    def __init__(self, name, nsamples, **options):
        self.name = name
        self.nsamples = nsamples
        self.options = options
        self._item = None

    def compute_data(self):
        raise NotImplementedError

    def make_item(self):
        data = self.compute_data()
        self._item = self.MAKE_FUNC(*data, **self.options)

    def add_to_plot(self, plot):
        assert self._item is not None
        plot.add_item(self._item)

    def start(self, close=False):
        # Create plot window
        win = PlotWindow(
            toolbar=True, wintitle=self.name, options={"type": self.WIN_TYPE}
        )
        win.show()
        QApplication.processEvents()
        plot = win.get_plot()

        # Create item (ignore this step in benchmark result!)
        self.make_item()

        # Benchmarking
        t0 = time.time()
        self.add_to_plot(plot)
        print(self.name + ":")
        print("    N  = {}".format(self.nsamples))
        plot.replot()  # Force replot
        print("    dt = {} ms".format((time.time() - t0) * 1e3))
        if close:
            win.close()


class CurveBM(BaseBM):
    MAKE_FUNC = make.curve
    WIN_TYPE = PlotType.CURVE

    def compute_data(self):
        x = np.linspace(-10, 10, self.nsamples)
        y = np.sin(np.sin(np.sin(x)))
        return x, y


class HistogramBM(CurveBM):
    MAKE_FUNC = make.histogram

    def compute_data(self):
        data = np.random.normal(size=int(self.nsamples))
        return (data,)


class ErrorBarBM(CurveBM):
    MAKE_FUNC = make.merror

    def __init__(self, name, nsamples, dx=False, **options):
        super(ErrorBarBM, self).__init__(name, nsamples, **options)
        self.dx = dx

    def compute_data(self):
        x, y = super(ErrorBarBM, self).compute_data()
        if not self.dx:
            return x, y, x / 100.0
        else:
            return x, y, x / 100.0, x / 20.0


class ImageBM(BaseBM):
    MAKE_FUNC = make.image
    WIN_TYPE = PlotType.IMAGE

    def compute_data(self):
        data = np.zeros((int(self.nsamples), int(self.nsamples)), dtype=np.float32)
        m = 10
        step = int(self.nsamples / m)
        for i in range(m):
            for j in range(m):
                data[i * step : (i + 1) * step, j * step : (j + 1) * step] = i * m + j
        return (data,)


class PColorBM(BaseBM):
    MAKE_FUNC = make.pcolor
    WIN_TYPE = PlotType.IMAGE

    def compute_data(self):
        N = self.nsamples
        r, th = np.meshgrid(np.linspace(1.0, 16, N), np.linspace(0.0, np.pi, N))
        x = r * np.cos(th)
        y = r * np.sin(th)
        z = 4 * th + r
        return x, y, z


def run():
    """Run benchmark"""
    # Print(informations banner)
    import plotpy
    from plotpy.gui.widgets.ext_gui_lib import PYQT_VERSION_STR, QT_VERSION_STR

    qt_lib = "PyQt5"
    title = "plotpy plot benchmark [{} v{} (Qt v{}), plotpy v{}]".format(
        qt_lib, PYQT_VERSION_STR, QT_VERSION_STR, plotpy.__version__
    )
    print(title)
    print("-" * len(title))
    print()

    import plotpy.gui

    _app = plotpy.gui.qapplication()

    # Run benchmarks
    close = False
    for benchmark in (
        CurveBM("Simple curve", 5e6),
        CurveBM("Curve with markers", 2e5, marker="Ellipse", markersize=10),
        CurveBM("Curve with sticks", 1e6, curvestyle="Sticks"),
        ErrorBarBM("Error bar curve (vertical bars only)", 1e4),
        ErrorBarBM("Error bar curve (horizontal and vertical bars)", 1e4, dx=True),
        HistogramBM("Simple histogram", 1e6, bins=int(1e5)),
        PColorBM("Polar pcolor", 1e3),
        ImageBM("Simple image", 7e3, interpolation="antialiasing"),
    ):
        benchmark.start(close=close)
    if not close:
        _app.exec_()


if __name__ == "__main__":
    run()
