# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see plotpy/LICENSE for details)

"""PlotDialog test"""

# FIXME: unexpected behavior when changing the xmin/xmax/ymin/ymax values in
#       the image parameters (2nd tab: "Axes")

# guitest: show

import numpy as np
from guidata.qthelpers import qt_app_context

from plotpy.core.builder import make
from plotpy.core.constants import PlotType
from plotpy.core.plot import PlotDialog


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


def compute_image_2():
    N = 1000
    T = np.float64
    TMAX = 32000
    TMIN = 32000
    S = 5.0
    x = np.array(np.linspace(-5 * S, 5 * S, N), T)
    img = np.zeros((N, N), T)
    x.shape = (1, N)
    img += x**2
    x.shape = (N, 1)
    img += x**2
    img = TMAX * np.cos(img / S) + TMIN
    x.shape = (N,)
    #    dx = dy = x[1]-x[0]
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
    img[:K, :K] = TMAX * m1 + TMIN  # (0,0)
    img[:K, -K:] = TMAX * m2 + TMIN  # (0,N)
    img[-K:, -K:] = TMAX * m3 + TMIN  # (N,N)
    img[-K:, :K] = TMAX * m4 + TMIN  # (N,0)
    # img = array( 30000*(img+1.1), uint16 )
    return img


def compute_image_3():
    """Produces horizontal and vertical ramps"""
    N = 1000
    NK = 20
    T = float
    img = np.zeros((N, N), T)
    x = np.arange(N, dtype=float)
    x.shape = (1, N)
    DK = N // NK
    for i in range(NK):
        S = i + 1
        y = S * (x // S)
        img[DK * i : DK * (i + 1), :] = y
    return img


def test_image():
    """Test image"""
    for func in (compute_image, compute_image_2, compute_image_3):
        data = func()
        with qt_app_context(exec_loop=True):
            win = PlotDialog(
                edit=False,
                toolbar=True,
                wintitle="PlotDialog test",
                options=dict(xlabel="Concentration", xunit="ppm", type=PlotType.IMAGE),
            )
            item = make.image(data)
            plot = win.manager.get_plot()
            plot.add_item(item)
            win.show()


if __name__ == "__main__":
    test_image()
