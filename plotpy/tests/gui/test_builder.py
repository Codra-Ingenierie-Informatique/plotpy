# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see plotpy/LICENSE for details)

"""Builder tests"""

# guitest: show

import numpy as np
from guidata.qthelpers import qt_app_context

from plotpy.builder import make
from plotpy.plot import PlotDialog, PlotOptions


def compute_image(N=2000, grid=True):
    T = np.float32
    x = np.array(np.linspace(-5, 5, N), T)
    img = np.zeros((N, N), T)
    x.shape = (1, N)
    img += x**2
    x.shape = (N, 1)
    img += x**2
    np.cos(img, img)  # inplace cosine
    if not grid:
        return img
    x.shape = (N,)
    for k in range(-5, 5):
        i = x.searchsorted(k)
        if k < 0:
            v = -1.1
        else:
            v = 1.1
        img[i, :] = v
        img[:, i] = v
    m1, m2, m3, m4 = -1.1, -0.3, 0.3, 1.1
    K = 100
    img[:K, :K] = m1  # (0,0)
    img[:K, -K:] = m2  # (0,N)
    img[-K:, -K:] = m3  # (N,N)
    img[-K:, :K] = m4  # (N,0)
    # img = array( 30000*(img+1.1), uint16 )
    return img


def test_builder():
    """Test"""
    # -- Create QApplication
    # import guidata

    # _app = guidata.qapplication()
    with qt_app_context(exec_loop=True):
        win0 = PlotDialog(
            edit=False,
            toolbar=True,
            title="Pink colormap test",
            options=PlotOptions(xlabel="Concentration", xunit="ppm", type="image"),
        )
        data = compute_image()
        plot0 = win0.manager.get_plot()
        plot0.add_item(make.image(data, colormap="pink"))
        win0.show()

        win = PlotDialog(
            edit=False,
            toolbar=True,
            title="Default LUT range",
            options=PlotOptions(xlabel="Concentration", xunit="ppm", type="image"),
        )
        item = make.image(data)
        plot = win.manager.get_plot()
        plot.add_item(item)
        win.show()

        win2 = PlotDialog(
            edit=False,
            toolbar=True,
            title="0->1 LUT range",
            options=PlotOptions(xlabel="Concentration", xunit="ppm", type="image"),
        )
        item2 = make.image(data)
        item2.set_lut_range([0, 1])
        plot2 = win2.manager.get_plot()
        plot2.add_item(item2)
        win2.show()

        win3 = PlotDialog(
            edit=False,
            toolbar=True,
            title="0->1 LUT range through builder",
            options=PlotOptions(xlabel="Concentration", xunit="ppm", type="image"),
        )
        item3 = make.image(data, lut_range=[0, 1])
        plot3 = win3.manager.get_plot()
        plot3.add_item(item3)
        win3.show()

        x = np.linspace(1, 10, 200)
        y = np.sin(x)

        win4 = PlotDialog(
            toolbar=True,
            title="Error bars with make.curve()",
            options=PlotOptions(type="curve"),
        )
        plot4 = win4.manager.get_plot()

        plot4.add_item(make.curve(x, y, dx=x * 0.1, dy=y * 0.23))
        plot4.add_item(make.curve(x, np.cos(x), color="#FF0000"))

        win4.show()

        win5 = PlotDialog(
            toolbar=True, title="2x2 image", options=PlotOptions(type="image")
        )
        plot5 = win5.manager.get_plot()

        img22 = np.zeros((2, 2), np.float32)
        img22[0, 0] = 1
        img22[0, 1] = 2
        img22[1, 0] = 3
        img22[1, 1] = 4
        plot5.add_item(
            make.image(img22, xdata=[-1, 3], ydata=[-1, 3], interpolation="nearest")
        )

        win5.show()

        win6 = PlotDialog(
            toolbar=True,
            title="Equivalent 2x2 XY image",
            options=PlotOptions(type="image"),
        )
        plot6 = win6.manager.get_plot()

        plot6.add_item(make.image(img22, x=[0, 2], y=[0, 2], interpolation="nearest"))

        win6.show()


if __name__ == "__main__":
    test_builder()
