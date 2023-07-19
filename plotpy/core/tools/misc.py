# -*- coding: utf -8 -*-
import os.path as osp
import sys

import numpy as np
from guidata.configtools import get_icon
from guidata.dataset.dataitems import BoolItem, ChoiceItem
from guidata.dataset.datatypes import BeginGroup, DataSet, EndGroup
from guidata.qthelpers import get_std_icon
from qtpy import QtCore as QC
from qtpy import QtWidgets as QW
from qtpy.QtPrintSupport import QPrintDialog, QPrinter

from plotpy.config import _
from plotpy.core import io
from plotpy.core.interfaces.common import IImageItemType
from plotpy.core.items.image.misc import (
    compute_trimageitems_original_size,
    get_image_from_plot,
    get_items_in_rectangle,
    get_plot_qrect,
)
from plotpy.core.tools.base import CommandTool, DefaultToolbarID, RectangularActionTool
from plotpy.widgets.about import about
from plotpy.widgets.resizedialog import ResizeDialog


class SaveAsTool(CommandTool):
    """ """

    def __init__(self, manager, toolbar_id=DefaultToolbarID):
        super(SaveAsTool, self).__init__(
            manager,
            _("Save as..."),
            get_std_icon("DialogSaveButton", 16),
            toolbar_id=toolbar_id,
        )

    def activate_command(self, plot, checked):
        """Activate tool"""
        # FIXME: Qt's PDF printer is unable to print plots including images
        # --> until this bug is fixed internally, disabling PDF output format
        #     when plot has image items.
        formats = "%s (*.png)" % _("PNG image")

        for item in plot.get_items():
            if IImageItemType in item.types():
                break
        else:
            formats += "\n%s (*.pdf)" % _("PDF document")
        fname, _f = QW.QFileDialog.getSaveFileName(
            plot, _("Save as"), _("untitled"), formats
        )
        if fname:
            plot.save_widget(fname)


class CopyToClipboardTool(CommandTool):
    """ """

    def __init__(self, manager, toolbar_id=DefaultToolbarID):
        super(CopyToClipboardTool, self).__init__(
            manager,
            _("Copy to clipboard"),
            get_icon("copytoclipboard.png"),
            toolbar_id=toolbar_id,
        )

    def activate_command(self, plot, checked):
        """Activate tool"""
        plot.copy_to_clipboard()


def save_snapshot(plot, p0, p1, new_size=None):
    """
    Save rectangular plot area
    p0, p1: resp. top left and bottom right points (`QPointF` objects)
    new_size: destination image size (tuple: (width, height))
    """
    items = get_items_in_rectangle(plot, p0, p1)
    if not items:
        QW.QMessageBox.critical(
            plot,
            _("Rectangle snapshot"),
            _("There is no supported image item in current selection."),
        )
        return
    src_x, src_y, src_w, src_h = get_plot_qrect(plot, p0, p1).getRect()
    original_size = compute_trimageitems_original_size(items, src_w, src_h)

    if new_size is None:
        new_size = (p1.x() - p0.x() + 1, p1.y() - p0.y() + 1)  # Screen size

    dlg = ResizeDialog(
        plot, new_size=new_size, old_size=original_size, text=_("Destination size:")
    )
    if not dlg.exec():
        return

    class SnapshotParam(DataSet):
        _levels = BeginGroup(_("Image levels adjustments"))
        apply_contrast = BoolItem(_("Apply contrast settings"), default=False)
        apply_interpolation = BoolItem(_("Apply interpolation algorithm"), default=True)
        norm_range = BoolItem(_("Scale levels to maximum range"), default=False)
        _end_levels = EndGroup(_("Image levels adjustments"))
        _multiple = BeginGroup(_("Superimposed images"))
        add_images = ChoiceItem(
            _("If image B is behind image A, " "replace intersection by"),
            [(False, "A"), (True, "A+B")],
            default=None,
        )
        _end_multiple = EndGroup(_("Superimposed images"))

    param = SnapshotParam(_("Rectangle snapshot"))
    if not param.edit(parent=plot):
        return

    if dlg.keep_original_size:
        destw, desth = original_size
    else:
        destw, desth = dlg.width, dlg.height

    try:
        data = get_image_from_plot(
            plot,
            p0,
            p1,
            destw=destw,
            desth=desth,
            add_images=param.add_images,
            apply_lut=param.apply_contrast,
            apply_interpolation=param.apply_interpolation,
            original_resolution=dlg.keep_original_size,
        )

        dtype = None
        for item in items:
            if dtype is None or item.data.dtype.itemsize > dtype.itemsize:
                dtype = item.data.dtype
        if param.norm_range:
            data = io.scale_data_to_dtype(data, dtype=dtype)
        else:
            data = np.array(data, dtype=dtype)
    except MemoryError:
        mbytes = int(destw * desth * 32.0 / (8 * 1024**2))
        text = _(
            "There is not enough memory left to process "
            "this {destw:d} x {desth:d} image ({mbytes:d} "
            "MB would be required)."
        )
        text = text.format(destw=destw, desth=desth, mbytes=mbytes)
        QW.QMessageBox.critical(plot, _("Memory error"), text)
        return
    for model_item in items:
        model_fname = model_item.get_filename()
        if model_fname is not None and model_fname.lower().endswith(".dcm"):
            break
    else:
        model_fname = None
    fname, _f = QW.QFileDialog.getSaveFileName(
        plot,
        _("Save as"),
        _("untitled"),
        io.iohandler.get_filters("save", data.dtype, template=True),
    )
    _base, ext = osp.splitext(fname)
    options = {}
    if not fname:
        return

    elif ext.lower() == ".png":
        options.update(dict(dtype=np.uint8, max_range=True))

    elif ext.lower() == ".dcm":
        # This import statement must stay here because if pydicom is not installed,
        # the extension .dcm is not registered in the io module, so we will not
        # get here.
        from pydicom import dicomio  # pylint: disable=import-outside-toplevel

        model_dcm = dicomio.read_file(model_fname)
        try:
            ps_attr = "ImagerPixelSpacing"
            ps_x, ps_y = getattr(model_dcm, ps_attr)
        except AttributeError:
            ps_attr = "PixelSpacing"
            ps_x, ps_y = getattr(model_dcm, ps_attr)
        model_dcm.Rows, model_dcm.Columns = data.shape

        dest_height, dest_width = data.shape
        (
            _x,
            _y,
            _angle,
            model_dx,
            model_dy,
            _hflip,
            _vflip,
        ) = model_item.get_transform()
        new_ps_x = ps_x * src_w / (model_dx * dest_width)
        new_ps_y = ps_y * src_h / (model_dy * dest_height)
        setattr(model_dcm, ps_attr, [new_ps_x, new_ps_y])
        options.update(dict(template=model_dcm))
    io.imwrite(fname, data, **options)


class SnapshotTool(RectangularActionTool):
    """ """

    SWITCH_TO_DEFAULT_TOOL = True
    TITLE = _("Rectangle snapshot")
    ICON = "snapshot.png"

    def __init__(self, manager, toolbar_id=DefaultToolbarID):
        super(SnapshotTool, self).__init__(
            manager, save_snapshot, toolbar_id=toolbar_id, fix_orientation=True
        )


class HelpTool(CommandTool):
    """ """

    def __init__(self, manager, toolbar_id=DefaultToolbarID):
        super(HelpTool, self).__init__(
            manager,
            _("Help"),
            get_std_icon("DialogHelpButton", 16),
            toolbar_id=toolbar_id,
        )

    def activate_command(self, plot, checked):
        """Activate tool"""
        QW.QMessageBox.information(
            plot,
            _("Help"),
            _(
                """Keyboard/mouse shortcuts:
  - single left-click: item (curve, image, ...) selection
  - single right-click: context-menu relative to selected item
  - shift: on-active-curve (or image) cursor
  - alt: free cursor
  - left-click + mouse move: move item (when available)
  - middle-click + mouse move: pan
  - right-click + mouse move: zoom"""
            ),
        )


class AboutTool(CommandTool):
    """ """

    def __init__(self, manager, toolbar_id=DefaultToolbarID):
        super(AboutTool, self).__init__(
            manager, _("About") + " plotpy", get_icon("plotpy.svg"), toolbar_id=None
        )

    def activate_command(self, plot, checked):
        """Activate tool"""

        QW.QMessageBox.about(plot, _("About") + " plotpy", about(html=True))


class PrintTool(CommandTool):
    """ """

    def __init__(self, manager, toolbar_id=DefaultToolbarID):
        super(PrintTool, self).__init__(
            manager, _("Print..."), get_icon("print.png"), toolbar_id=toolbar_id
        )

    def activate_command(self, plot, checked):
        """Activate tool"""
        printer = QPrinter()
        dialog = QPrintDialog(printer, plot)
        saved_in, saved_out, saved_err = sys.stdin, sys.stdout, sys.stderr
        sys.stdout = None
        ok = dialog.exec()
        sys.stdin, sys.stdout, sys.stderr = saved_in, saved_out, saved_err
        if ok:
            plot.print_(printer)


class OpenFileTool(CommandTool):
    """ """

    #: Signal emitted by OpenFileTool when a file was opened
    #:
    #: Args:
    #:     filename (str): The name of the file that was opened
    SIG_OPEN_FILE = QC.Signal(str)

    def __init__(
        self, manager, title=_("Open..."), formats="*.*", toolbar_id=DefaultToolbarID
    ):
        super(OpenFileTool, self).__init__(
            manager, title, get_std_icon("DialogOpenButton", 16), toolbar_id=toolbar_id
        )
        self.formats = formats
        self.directory = ""

    def get_filename(self, plot):
        """

        :param plot:
        :return:
        """
        saved_in, saved_out, saved_err = sys.stdin, sys.stdout, sys.stderr
        sys.stdout = None
        filename, _f = QW.QFileDialog.getOpenFileName(
            plot, _("Open"), self.directory, self.formats
        )
        sys.stdin, sys.stdout, sys.stderr = saved_in, saved_out, saved_err
        filename = str(filename)
        if filename:
            self.directory = osp.dirname(filename)
        return filename

    def activate_command(self, plot, checked):
        """Activate tool"""
        filename = self.get_filename(plot)
        if filename:
            self.SIG_OPEN_FILE.emit(filename)


class FilterTool(CommandTool):
    """ """

    def __init__(self, manager, filter, toolbar_id=None):
        super(FilterTool, self).__init__(
            manager, str(filter.name), toolbar_id=toolbar_id
        )
        self.filter = filter

    def update_status(self, plot):
        """

        :param plot:
        """
        self.set_status_active_item(plot)

    def activate_command(self, plot, checked):
        """Activate tool"""
        plot.apply_filter(self.filter)
