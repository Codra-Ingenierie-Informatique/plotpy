# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see plotpy/LICENSE for details)

"""
Masked Image test, creating the MaskedImageItem object via make.maskedimage

Masked image items are constructed using a masked array item. Masked data is
ignored in computations, like the average cross sections.
"""

# guitest: show

import os.path as osp

from plotpy.builder import make
from plotpy.tests.gui.test_loadsaveitems_pickle import PickleTest


class MaskedImageTest(PickleTest):
    """Test class for MaskedImageItem tests"""

    FNAME = f"{osp.splitext(osp.basename(__file__))[0]}.pickle"
    IMAGE_FN = osp.join(osp.abspath(osp.dirname(__file__)), "brain.png")

    def build_items(self) -> list:
        """Build items"""
        image = make.maskedimage(
            filename=self.IMAGE_FN,
            colormap="gray",
            show_mask=True,
            xdata=[0, 20],
            ydata=[0, 25],
        )
        return [image]


def test_image_masked():
    """Test MaskedImageItem"""
    test = MaskedImageTest("MaskedImageItem test")
    test.run()


if __name__ == "__main__":
    test_image_masked()
