# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see plotpy/LICENSE for details)

"""PlotTypes test"""

# guitest: show

import numpy as np
from guidata.qthelpers import qt_app_context
from numpy import linspace, sin

from plotpy.builder import make
from plotpy.constants import PlotType
from plotpy.plot import PlotDialog


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


def plot(*items, type=PlotType.AUTO, title=""):
    win = PlotDialog(
        edit=False,
        toolbar=True,
        wintitle=title,
        options=dict(title=title, xlabel="xlabel", ylabel="ylabel", type=type),
    )

    plot = win.manager.get_plot()
    for item in items:
        plot.add_item(item)
    win.manager.get_itemlist_panel().show()
    plot.set_items_readonly(False)
    win.show()
    return win


def test_plot_types():
    """Test plot types"""
    _perist_plot_list = []
    with qt_app_context(exec_loop=True):
        x = linspace(-10, 10, 200)
        y = sin(sin(sin(x)))

        _perist_plot_list.append(
            plot(
                make.curve(x, y, color="b"),
                make.image(compute_image()),
                type=PlotType.CURVE,
                title="Curve specialized plot",
            )
        )

        _perist_plot_list.append(
            plot(
                make.curve(x, y, color="b"),
                make.image(compute_image()),
                type=PlotType.IMAGE,
                title="Image specialized plot",
            )
        )

        _perist_plot_list.append(
            plot(
                make.curve(x, y, color="b"),
                make.image(compute_image()),
                title="PlotType = AUTO with curve added first",
            )
        )

        _perist_plot_list.append(
            plot(
                make.image(compute_image()),
                make.curve(x, y, color="b"),
                title="PlotType = AUTO with image added first",
            )
        )

        _perist_plot_list.append(
            plot(
                make.curve(x, y, color="b"),
                make.image(compute_image()),
                type=PlotType.MANUAL,
                title="PlotType = MANUAL",
            )
        )


if __name__ == "__main__":
    test_plot_types()
