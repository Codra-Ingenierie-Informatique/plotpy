# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see plotpy/__init__.py for details)

"""
DataSet objects inheritance test

From time to time, it may be useful to derive a DataSet from another. The main
application is to extend a parameter set with additionnal parameters.
"""


from guidata.dataset.dataitems import BoolItem, FloatItem
from guidata.dataset.datatypes import BeginGroup, EndGroup

try:
    from tests.scripts.all_features import TestParameters
except ImportError:
    from plotpy.tests.scripts.all_features import TestParameters

SHOW = True  # Show test in GUI-based test launcher


class TestParameters2(TestParameters):
    bool1 = BoolItem("Boolean option (bis)")
    g1 = BeginGroup("Group")
    a = FloatItem("Level 1")
    gg1 = BeginGroup("sub-group")
    b = FloatItem("Level 2a")
    c = FloatItem("Level 2b")
    _gg1 = EndGroup("sub-group end")
    _g1 = EndGroup("sub-group")


if __name__ == "__main__":
    # Create QApplication
    import plotpy.config
    import plotpy.widgets

    _app = plotpy.widgets.qapplication()

    e = TestParameters2()
    e.edit()
    print(e)
