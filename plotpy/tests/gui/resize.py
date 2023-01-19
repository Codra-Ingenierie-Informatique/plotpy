# -*- coding: utf-8 -*-
#
# Copyright © 2012 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see plotpy/__init__.py for details)

"""Resize test: using the scaler C++ engine to resize images"""

SHOW = True  # Show test in GUI-based test launcher


def test():
    """Test"""
    import os.path as osp

    from plotpy.widgets import io, qapplication, scaler
    from plotpy.widgets.plot.interactive import imshow, show

    app = qapplication()

    filename = osp.join(osp.dirname(__file__), "brain.png")
    data = io.imread(filename)
    dst_image = scaler.resize(data, (2000, 3000))

    imshow(dst_image, interpolation="nearest")
    show()


if __name__ == "__main__":
    test()
