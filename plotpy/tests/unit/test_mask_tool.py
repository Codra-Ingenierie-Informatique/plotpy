import contextlib

import numpy as np
import pytest
from guidata.env import execenv
from guidata.qthelpers import exec_dialog, qt_app_context

from plotpy.builder import make
from plotpy.interfaces.items import IImageItemType
from plotpy.plot import BasePlot
from plotpy.tests.data import gen_image4
from plotpy.tests.unit.utils import (
    drag_mouse,
    mouse_event_at_relative_plot_pos,
    rel_pos_to_canvas_pos,
)
from plotpy.tools import ColormapTool, ReverseColormapTool
from plotpy.tools.image import ImageMaskTool, LockTrImageTool
from plotpy.tools.shape import CircleTool, RectangleTool, RectangularShapeTool


@pytest.mark.parametrize("shape_tool_cls", [RectangleTool, CircleTool])
@pytest.mark.parametrize("inside", [True, False])
def test_image_mask_tool(shape_tool_cls: type[RectangularShapeTool], inside: bool):
    """Test ImageMaskTool"""
    with qt_app_context(exec_loop=False):
        win = make.dialog(type="image", toolbar=True)
        item = make.maskedimage(gen_image4(100, 100))
        plot = win.manager.get_plot()
        plot.add_item(item)  # type: ignore
        plot.select_item(item)  # type: ignore
        win.show()
        mask_tool = win.manager.add_tool(
            ImageMaskTool,
        )
        shape_tool = win.manager.add_tool(
            shape_tool_cls,
            toolbar_id=None,
            handle_final_shape_cb=lambda shape: mask_tool.handle_shape(
                shape, inside=inside
            ),
        )
        shape_tool.activate()
        xy0, xy1 = (0.1, 0.1), (0.9, 0.9)
        canvas = plot.canvas()
        assert canvas is not None
        pos0, _ = rel_pos_to_canvas_pos(canvas, xy0)
        pos1, _ = rel_pos_to_canvas_pos(canvas, xy1)

        with execenv.context(accept_dialogs=True):
            shape_tool.add_shape_to_plot(plot, pos0, pos1)
            mask_tool.apply_mask()
            mask_tool.clear_mask()

            shape_tool.add_shape_to_plot(plot, pos0, pos1)
            mask_tool.remove_all_shapes()

        exec_dialog(win)
