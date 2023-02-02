# -*- coding: utf-8 -*-
import os
import os.path as osp
import sys

import numpy as np
from guidata.configtools import get_icon
from guidata.utils import update_dataset
from qtpy import QtCore as QC
from qtpy import QtGui as QG
from qwt import QwtPlotItem

from plotpy._scaler import (
    INTERP_AA,
    INTERP_LINEAR,
    INTERP_NEAREST,
    _histogram,
    _scale_rect,
)
from plotpy.config import _
from plotpy.utils.gui import assert_interfaces_valid
from plotpy.widgets import io
from plotpy.widgets.colormap import FULLRANGE, get_cmap, get_cmap_name
from plotpy.widgets.interfaces.common import (
    IBaseImageItem,
    IBasePlotItem,
    IColormapImageItemType,
    ICSImageItemType,
    IExportROIImageItemType,
    IHistDataSource,
    IImageItemType,
    ISerializableType,
    IStatsImageItemType,
    ITrackableItemType,
    IVoiImageItemType,
)
from plotpy.widgets.items.shapes.rectangle import RectangleShape
from plotpy.widgets.styles.image import RawImageParam

LUT_SIZE = 1024
LUT_MAX = float(LUT_SIZE - 1)


def _nanmin(data):
    if isinstance(data, np.ma.MaskedArray):
        data = data.data
    if data.dtype.name in ("float32", "float64", "float128"):
        return np.nanmin(data)
    else:
        return data.min()


def _nanmax(data):
    if isinstance(data, np.ma.MaskedArray):
        data = data.data
    if data.dtype.name in ("float32", "float64", "float128"):
        return np.nanmax(data)
    else:
        return data.max()


def pixelround(x, corner=None):
    """
    Return pixel index (int) from pixel coordinate (float)
    corner: None (not a corner), 'TL' (top-left corner),
    'BR' (bottom-right corner)
    """
    assert corner is None or corner in ("TL", "BR")
    if corner is None:
        return np.floor(x)
    elif corner == "BR":
        return np.ceil(x)
    elif corner == "TL":
        return np.floor(x)


class BaseImageItem(QwtPlotItem):
    """ """

    __implements__ = (
        IBasePlotItem,
        IBaseImageItem,
        IHistDataSource,
        IVoiImageItemType,
        ICSImageItemType,
        IStatsImageItemType,
        IExportROIImageItemType,
    )
    _can_select = True
    _can_resize = False
    _can_move = False
    _can_rotate = False
    _readonly = False
    _private = False

    def __init__(self, data=None, param=None):
        super(BaseImageItem, self).__init__()

        self.bg_qcolor = QG.QColor()

        self.bounds = QC.QRectF()

        # BaseImageItem needs:
        # param.background
        # param.alpha_mask
        # param.alpha
        # param.colormap
        if param is None:
            param = self.get_default_param()
        self.param = param

        self.selected = False

        self.data = None

        self.min = 0.0
        self.max = 1.0
        self.cmap_table = None
        self.cmap = None
        self.colormap_axis = None

        self._offscreen = np.array((1, 1), np.uint32)

        # Linear interpolation is the default interpolation algorithm:
        # it's almost as fast as 'nearest pixel' method but far smoother
        self.interpolate = None
        self.set_interpolation(INTERP_LINEAR)

        x1, y1 = self.bounds.left(), self.bounds.top()
        x2, y2 = self.bounds.right(), self.bounds.bottom()
        self.border_rect = RectangleShape(x1, y1, x2, y2)
        self.border_rect.set_style("plot", "shape/imageborder")
        # A, B, Background, Colormap
        self.lut = (1.0, 0.0, None, np.zeros((LUT_SIZE,), np.uint32))

        self.set_lut_range([0.0, 255.0])
        self.setItemAttribute(QwtPlotItem.AutoScale)
        self.setItemAttribute(QwtPlotItem.Legend, True)
        self._filename = None  # The file this image comes from

        self.histogram_cache = None
        if data is not None:
            self.set_data(data)
        self.param.update_item(self)
        self.setIcon(get_icon("image.png"))

    # ---- Public API ----------------------------------------------------------
    def get_default_param(self):
        """Return instance of the default imageparam DataSet"""
        raise NotImplementedError

    def set_filename(self, fname):
        """

        :param fname:
        """
        self._filename = fname

    def get_filename(self):
        """

        :return:
        """
        fname = self._filename
        if fname is not None and not osp.isfile(fname):
            other_try = osp.join(os.getcwd(), osp.basename(fname))
            if osp.isfile(other_try):
                self.set_filename(other_try)
                fname = other_try
        return fname

    def get_filter(self, filterobj, filterparam):
        """Provides a filter object over this image's content"""
        raise NotImplementedError

    def get_pixel_coordinates(self, xplot, yplot):
        """
        Return (image) pixel coordinates
        Transform the plot coordinates (arbitrary plot Z-axis unit)
        into the image coordinates (pixel unit)

        Rounding is necessary to obtain array indexes from these coordinates
        """
        return xplot, yplot

    def get_plot_coordinates(self, xpixel, ypixel):
        """
        Return plot coordinates
        Transform the image coordinates (pixel unit)
        into the plot coordinates (arbitrary plot Z-axis unit)
        """
        return xpixel, ypixel

    def get_closest_indexes(self, x, y, corner=None):
        """
        Return closest image pixel indexes
        corner: None (not a corner), 'TL' (top-left corner),
        'BR' (bottom-right corner)
        """
        x, y = self.get_pixel_coordinates(x, y)
        i_max = self.data.shape[1] - 1
        j_max = self.data.shape[0] - 1
        if corner == "BR":
            i_max += 1
            j_max += 1
        i = max([0, min([i_max, int(pixelround(x, corner))])])
        j = max([0, min([j_max, int(pixelround(y, corner))])])
        return i, j

    def get_closest_index_rect(self, x0, y0, x1, y1):
        """
        Return closest image rectangular pixel area index bounds
        Avoid returning empty rectangular area (return 1x1 pixel area instead)
        Handle reversed/not-reversed Y-axis orientation
        """
        ix0, iy0 = self.get_closest_indexes(x0, y0, corner="TL")
        ix1, iy1 = self.get_closest_indexes(x1, y1, corner="BR")
        if ix0 > ix1:
            ix1, ix0 = ix0, ix1
        if iy0 > iy1:
            iy1, iy0 = iy0, iy1
        if ix0 == ix1:
            ix1 += 1
        if iy0 == iy1:
            iy1 += 1
        return ix0, iy0, ix1, iy1

    def align_rectangular_shape(self, shape):
        """Align rectangular shape to image pixels"""
        ix0, iy0, ix1, iy1 = self.get_closest_index_rect(*shape.get_rect())
        x0, y0 = self.get_plot_coordinates(ix0, iy0)
        x1, y1 = self.get_plot_coordinates(ix1, iy1)
        shape.set_rect(x0, y0, x1, y1)

    def get_closest_pixel_indexes(self, x, y):
        """
        Return closest pixel indexes
        Instead of returning indexes of an image pixel like the method
        'get_closest_indexes', this method returns the indexes of the
        closest pixel which is not necessarily on the image itself
        (i.e. indexes may be outside image index bounds: negative or
        superior than the image dimension)

        .. note::

            This is *not* the same as retrieving the canvas pixel coordinates
            (which depends on the zoom level)
        """
        x, y = self.get_pixel_coordinates(x, y)
        i = int(pixelround(x))
        j = int(pixelround(y))
        return i, j

    def get_x_values(self, i0, i1):
        """

        :param i0:
        :param i1:
        :return:
        """
        return np.arange(i0, i1)

    def get_y_values(self, j0, j1):
        """

        :param j0:
        :param j1:
        :return:
        """
        return np.arange(j0, j1)

    def get_r_values(self, i0, i1, j0, j1, flag_circle=False):
        return self.get_x_values(i0, i1)

    def get_data(self, x0, y0, x1=None, y1=None):
        """
        Return image data
        Arguments: x0, y0 [, x1, y1]
        Return image level at coordinates (x0,y0)

        If x1,y1 are specified:

          Return image levels (np.ndarray) in rectangular area (x0,y0,x1,y1)
        """
        i0, j0 = self.get_closest_indexes(x0, y0)
        if x1 is None or y1 is None:
            return self.data[j0, i0]
        else:
            i1, j1 = self.get_closest_indexes(x1, y1)
            i1 += 1
            j1 += 1
            return (
                self.get_x_values(i0, i1),
                self.get_y_values(j0, j1),
                self.data[j0:j1, i0:i1],
            )

    def get_closest_coordinates(self, x, y):
        """Return closest image pixel coordinates"""
        return self.get_closest_indexes(x, y)

    def get_coordinates_label(self, xc, yc):
        """

        :param xc:
        :param yc:
        :return:
        """
        title = self.title().text()
        z = self.get_data(xc, yc)
        xc = int(xc)
        yc = int(yc)
        return f"{title}:<br>x = {xc:d}<br>y = {yc:d}<br>z = {z:g}"

    def set_background_color(self, qcolor):
        """

        :param qcolor:
        """
        # mask = np.uint32(255*self.param.alpha+0.5).clip(0,255) << 24
        self.bg_qcolor = qcolor
        a, b, _bg, cmap = self.lut
        if qcolor is None:
            self.lut = (a, b, None, cmap)
        else:
            self.lut = (a, b, np.uint32(QG.QColor(qcolor).rgb() & 0xFFFFFF), cmap)

    def set_color_map(self, name_or_table):
        """

        :param name_or_table:
        :return:
        """
        if name_or_table is self.cmap_table:
            # This avoids rebuilding the LUT all the time
            return
        if isinstance(name_or_table, str):
            table = get_cmap(name_or_table)
        else:
            table = name_or_table
        self.cmap_table = table
        self.cmap = table.colorTable(FULLRANGE)
        cmap_a = self.lut[3]
        alpha = self.param.alpha
        alpha_mask = self.param.alpha_mask
        for i in range(LUT_SIZE):
            if alpha_mask:
                pix_alpha = alpha * (i / float(LUT_SIZE - 1))
            else:
                pix_alpha = alpha
            alpha_channel = np.uint32(255 * pix_alpha + 0.5).clip(0, 255) << 24
            cmap_a[i] = (
                np.uint32((table.rgb(FULLRANGE, i / LUT_MAX)) & 0xFFFFFF)
                | alpha_channel
            )
        plot = self.plot()
        if plot:
            plot.update_colormap_axis(self)

    def get_color_map(self):
        """

        :return:
        """
        return self.cmap_table

    def get_color_map_name(self):
        """

        :return:
        """
        return get_cmap_name(self.get_color_map())

    def set_interpolation(self, interp_mode, size=None):
        """
        Set image interpolation mode

        interp_mode: INTERP_NEAREST, INTERP_LINEAR, INTERP_AA
        size (integer): (for anti-aliasing only) AA matrix size
        """
        if interp_mode in (INTERP_NEAREST, INTERP_LINEAR):
            self.interpolate = (interp_mode,)
        if interp_mode == INTERP_AA:
            aa = np.ones((size, size), self.data.dtype)
            self.interpolate = (interp_mode, aa)

    def get_interpolation(self):
        """Get interpolation mode"""
        return self.interpolate

    def set_lut_range(self, lut_range):
        """
        Set LUT transform range
        *lut_range* is a tuple: (min, max)
        """
        self.min, self.max = lut_range
        _a, _b, bg, cmap = self.lut
        if self.max == self.min:
            self.lut = (LUT_MAX, self.min, bg, cmap)
        else:
            fmin, fmax = float(self.min), float(self.max)  # avoid overflows
            self.lut = (
                LUT_MAX / (fmax - fmin),
                -LUT_MAX * fmin / (fmax - fmin),
                bg,
                cmap,
            )

    def get_lut_range(self):
        """Return the LUT transform range tuple: (min, max)"""
        return self.min, self.max

    def get_lut_range_full(self):
        """Return full dynamic range"""
        return _nanmin(self.data), _nanmax(self.data)

    def get_lut_range_max(self):
        """Get maximum range for this dataset"""
        kind = self.data.dtype.kind
        if kind in np.typecodes["AllFloat"]:
            info = np.finfo(self.data.dtype)
        else:
            info = np.iinfo(self.data.dtype)
        return info.min, info.max

    def update_border(self):
        """Update image border rectangle to fit image shape"""
        bounds = self.boundingRect().getCoords()
        self.border_rect.set_rect(*bounds)

    def draw_border(self, painter, xMap, yMap, canvasRect):
        """Draw image border rectangle"""
        self.border_rect.draw(painter, xMap, yMap, canvasRect)

    def draw_image(self, painter, canvasRect, src_rect, dst_rect, xMap, yMap):
        """
        Draw image with painter on canvasRect

        .. warning::

            `src_rect` and `dst_rect` are coordinates tuples
            (xleft, ytop, xright, ybottom)
        """
        dest = _scale_rect(
            self.data, src_rect, self._offscreen, dst_rect, self.lut, self.interpolate
        )
        qrect = QC.QRectF(QC.QPointF(dest[0], dest[1]), QC.QPointF(dest[2], dest[3]))
        painter.drawImage(qrect, self._image, qrect)

    def export_roi(
        self,
        src_rect,
        dst_rect,
        dst_image,
        apply_lut=False,
        apply_interpolation=False,
        original_resolution=False,
        force_interp_mode=None,
        force_interp_size=None,
    ):
        """Export Region Of Interest to array"""
        if apply_lut:
            a, b, _bg, _cmap = self.lut
        else:
            a, b = 1.0, 0.0
        interp = self.interpolate if apply_interpolation else (INTERP_NEAREST,)
        _scale_rect(self.data, src_rect, dst_image, dst_rect, (a, b, None), interp)

    # ---- QwtPlotItem API -----------------------------------------------------
    def draw(self, painter, xMap, yMap, canvasRect):
        """

        :param painter:
        :param xMap:
        :param yMap:
        :param canvasRect:
        """
        x1, y1, x2, y2 = canvasRect.getCoords()
        i1, i2 = xMap.invTransform(x1), xMap.invTransform(x2)
        j1, j2 = yMap.invTransform(y1), yMap.invTransform(y2)

        xl, yt, xr, yb = self.boundingRect().getCoords()
        dest = (
            xMap.transform(xl),
            yMap.transform(yt),
            xMap.transform(xr) + 1,
            yMap.transform(yb) + 1,
        )

        W = canvasRect.right()
        H = canvasRect.bottom()
        if self._offscreen.shape != (H, W):
            self._offscreen = np.empty((int(H), int(W)), np.uint32)
            self._image = QG.QImage(self._offscreen, W, H, QG.QImage.Format_ARGB32)
            self._image.ndarray = self._offscreen
            self.notify_new_offscreen()
        self.draw_image(painter, canvasRect, (i1, j1, i2, j2), dest, xMap, yMap)
        self.draw_border(painter, xMap, yMap, canvasRect)

    def boundingRect(self):
        """

        :return:
        """
        return self.bounds

    def notify_new_offscreen(self):
        """ """
        # callback for those derived classes who need it
        pass

    def setVisible(self, enable):
        """

        :param enable:
        """
        if not enable:
            self.unselect()  # when hiding item, unselect it
        if enable:
            self.border_rect.show()
        else:
            self.border_rect.hide()
        QwtPlotItem.setVisible(self, enable)

    # ---- IBasePlotItem API ----------------------------------------------------
    def types(self):
        """

        :return:
        """
        return (
            IImageItemType,
            IVoiImageItemType,
            IColormapImageItemType,
            ITrackableItemType,
            ICSImageItemType,
            IExportROIImageItemType,
            IStatsImageItemType,
            IStatsImageItemType,
        )

    def set_readonly(self, state):
        """Set object readonly state"""
        self._readonly = state

    def is_readonly(self):
        """Return object readonly state"""
        return self._readonly

    def set_private(self, state):
        """Set object as private"""
        self._private = state

    def is_private(self):
        """Return True if object is private"""
        return self._private

    def select(self):
        """Select item"""
        self.selected = True
        self.border_rect.select()

    def unselect(self):
        """Unselect item"""
        self.selected = False
        self.border_rect.unselect()

    def is_empty(self):
        """Return True if item data is empty"""
        return self.data is None or self.data.size == 0

    def set_selectable(self, state):
        """Set item selectable state"""
        self._can_select = state

    def set_resizable(self, state):
        """Set item resizable state
        (or any action triggered when moving an handle, e.g. rotation)"""
        self._can_resize = state

    def set_movable(self, state):
        """Set item movable state"""
        self._can_move = state

    def set_rotatable(self, state):
        """Set item rotatable state"""
        self._can_rotate = state

    def can_select(self):
        """

        :return:
        """
        return self._can_select

    def can_resize(self):
        """

        :return:
        """
        return self._can_resize and not getattr(self.param, "lock_position", False)

    def can_move(self):
        """

        :return:
        """
        return self._can_move and not getattr(self.param, "lock_position", False)

    def can_rotate(self):
        """

        :return:
        """
        return self._can_rotate and not getattr(self.param, "lock_position", False)

    def hit_test(self, pos):
        """

        :param pos:
        :return:
        """
        plot = self.plot()
        ax = self.xAxis()
        ay = self.yAxis()
        return self.border_rect.poly_hit_test(plot, ax, ay, pos)

    def update_item_parameters(self):
        """ """
        pass

    def get_item_parameters(self, itemparams):
        """

        :param itemparams:
        """
        itemparams.add("ShapeParam", self, self.border_rect.shapeparam)

    def set_item_parameters(self, itemparams):
        """

        :param itemparams:
        """
        self.border_rect.set_item_parameters(itemparams)

    def move_local_point_to(self, handle, pos, ctrl=None):
        """Move a handle as returned by hit_test to the new position pos
        ctrl: True if <Ctrl> button is being pressed, False otherwise"""
        pass

    def move_local_shape(self, old_pos, new_pos):
        """Translate the shape such that old_pos becomes new_pos
        in canvas coordinates"""
        pass

    def move_with_selection(self, delta_x, delta_y):
        """
        Translate the shape together with other selected items
        delta_x, delta_y: translation in plot coordinates
        """
        pass

    def resize_with_selection(self, zoom_dx, zoom_dy):
        """
        Resize the shape together with other selected items
        zoom_dx, zoom_dy : zoom factor for dx and dy
        """
        pass

    def rotate_with_selection(self, angle):
        """
        Rotate the shape together with other selected items
        angle : rotation angle
        """
        pass

    # ---- IBaseImageItem API --------------------------------------------------
    def can_setfullscale(self):
        """

        :return:
        """
        return True

    def can_sethistogram(self):
        """

        :return:
        """
        return False

    def get_histogram(self, nbins):
        """interface de IHistDataSource"""
        if self.data is None:
            return [0], [0, 1]
        if self.histogram_cache is None or nbins != self.histogram_cache[0].shape[0]:
            if True:
                # tic("histo1")
                # Note: np.histogram does not accept data with NaN
                res = np.histogram(self.data[~np.isnan(self.data)], nbins)
                # toc("histo1")
            else:
                # TODO: _histogram is faster, but caching is buggy
                # in this version
                # tic("histo2")
                _min = _nanmin(self.data)
                _max = _nanmax(self.data)
                if self.data.dtype in (np.float64, np.float32):
                    bins = np.unique(
                        np.array(
                            np.linspace(_min, _max, nbins + 1), dtype=self.data.dtype
                        )
                    )
                else:
                    bins = np.arange(_min, _max + 2, dtype=self.data.dtype)
                res2 = np.zeros((bins.size + 1,), np.uint32)
                _histogram(self.data.flatten(), bins, res2)
                # toc("histo2")
                res = res2[1:-1], bins
            self.histogram_cache = res
        else:
            res = self.histogram_cache
        return res

    def __process_cross_section(self, ydata, apply_lut):
        if apply_lut:
            a, b, bg, cmap = self.lut
            return (ydata * a + b).clip(0, LUT_MAX)
        else:
            return ydata

    def get_stats(self, x0, y0, x1, y1, show_surface=False, show_integral=False):
        """Return formatted string with stats on image rectangular area
        (output should be compatible with AnnotatedShape.get_infos)"""
        ix0, iy0, ix1, iy1 = self.get_closest_index_rect(x0, y0, x1, y1)
        data = self.data[iy0:iy1, ix0:ix1]
        xfmt = self.param.xformat
        yfmt = self.param.yformat
        zfmt = self.param.zformat
        try:
            xunit = xfmt.split()[1]
        except IndexError:
            xunit = ""
        try:
            yunit = yfmt.split()[1]
        except IndexError:
            yunit = ""
        try:
            zunit = zfmt.split()[1]
        except IndexError:
            zunit = ""
        if show_integral:
            integral = data.sum()
        infos = "<br>".join(
            [
                "<b>%s</b>" % self.param.label,
                "%sx%s %s"
                % (self.data.shape[1], self.data.shape[0], str(self.data.dtype)),
                "",
                "%s ≤ x ≤ %s" % (xfmt % x0, xfmt % x1),
                "%s ≤ y ≤ %s" % (yfmt % y0, yfmt % y1),
                "%s ≤ z ≤ %s" % (zfmt % data.min(), zfmt % data.max()),
                "‹z› = " + zfmt % data.mean(),
                "σ(z) = " + zfmt % data.std(),
            ]
        )
        if show_surface and xunit == yunit:
            surfacefmt = xfmt.split()[0] + " " + xunit
            if xunit != "":
                surfacefmt = surfacefmt + "²"
            surface = abs((x1 - x0) * (y1 - y0))
            infos = infos + "<br>" + _("surface = %s") % (surfacefmt % surface)
        if show_integral:
            integral = data.sum()
            integral_fmt = r"%.3e " + zunit
            infos = infos + "<br>" + _("sum = %s") % (integral_fmt % integral)
        if (
            show_surface
            and xunit == yunit
            and xunit is not None
            and show_integral
            and zunit is not None
        ):
            if surface != 0:
                density = integral / surface
                densityfmt = r"%.3e " + zunit + "/" + xunit
                if xunit != "":
                    densityfmt = densityfmt + "²"
                infos = infos + "<br>" + _("density = %s") % (densityfmt % density)
            else:
                infos = infos + "<br>" + _("density not computed : surface is null !")
        return infos

    def get_xsection(self, y0, apply_lut=False):
        """Return cross section along x-axis at y=y0"""
        _ix, iy = self.get_closest_indexes(0, y0)
        return (
            self.get_x_values(0, self.data.shape[1]),
            self.__process_cross_section(self.data[iy, :], apply_lut),
        )

    def get_ysection(self, x0, apply_lut=False):
        """Return cross section along y-axis at x=x0"""
        ix, _iy = self.get_closest_indexes(x0, 0)
        return (
            self.get_y_values(0, self.data.shape[0]),
            self.__process_cross_section(self.data[:, ix], apply_lut),
        )

    def get_average_xsection(self, x0, y0, x1, y1, apply_lut=False):
        """Return average cross section along x-axis"""
        ix0, iy0, ix1, iy1 = self.get_closest_index_rect(x0, y0, x1, y1)
        ydata = self.data[iy0:iy1, ix0:ix1]
        if ydata.size == 0:
            return np.array([]), np.array([])
        ydata = ydata.mean(axis=0)
        return (
            self.get_x_values(ix0, ix1),
            self.__process_cross_section(ydata, apply_lut),
        )

    def get_average_ysection(self, x0, y0, x1, y1, apply_lut=False):
        """Return average cross section along y-axis"""
        ix0, iy0, ix1, iy1 = self.get_closest_index_rect(x0, y0, x1, y1)
        ydata = self.data[iy0:iy1, ix0:ix1]
        if ydata.size == 0:
            return np.array([]), np.array([])
        ydata = ydata.mean(axis=1)
        return (
            self.get_y_values(iy0, iy1),
            self.__process_cross_section(ydata, apply_lut),
        )


assert_interfaces_valid(BaseImageItem)


# ==============================================================================
# Raw Image item (image item without scale)
# ==============================================================================
class RawImageItem(BaseImageItem):
    """
    Construct a simple image item

        * data: 2D NumPy array
        * param (optional): image parameters
          (:py:class:`.styles.RawImageParam` instance)
    """

    __implements__ = (
        IBasePlotItem,
        IBaseImageItem,
        IHistDataSource,
        IVoiImageItemType,
        ISerializableType,
    )

    # ---- BaseImageItem API ---------------------------------------------------
    def get_default_param(self):
        """Return instance of the default imageparam DataSet"""
        return RawImageParam(_("Image"))

    # ---- Serialization methods -----------------------------------------------
    def __reduce__(self):
        fname = self.get_filename()
        if fname is None:
            fn_or_data = self.data
        else:
            fn_or_data = fname
        state = self.param, self.get_lut_range(), fn_or_data, self.z()
        res = (self.__class__, (), state)
        return res

    def __setstate__(self, state):
        param, lut_range, fn_or_data, z = state
        self.param = param
        if isinstance(fn_or_data, str):
            self.set_filename(fn_or_data)
            self.load_data()
        elif fn_or_data is not None:  # should happen only with previous API
            self.set_data(fn_or_data)
        self.set_lut_range(lut_range)
        self.setZ(z)
        self.param.update_item(self)

    def serialize(self, writer):
        """Serialize object to HDF5 writer"""
        fname = self.get_filename()
        load_from_fname = fname is not None
        data = None if load_from_fname else self.data
        writer.write(load_from_fname, group_name="load_from_fname")
        writer.write(fname, group_name="fname")
        writer.write(data, group_name="Zdata")
        writer.write(self.get_lut_range(), group_name="lut_range")
        writer.write(self.z(), group_name="z")
        self.param.update_param(self)
        writer.write(self.param, group_name="imageparam")

    def deserialize(self, reader):
        """Deserialize object from HDF5 reader"""
        lut_range = reader.read(group_name="lut_range")
        if reader.read(group_name="load_from_fname"):
            name = reader.read(group_name="fname", func=reader.read_unicode)
            name = io.iohandler.adapt_path(name)
            self.set_filename(name)
            self.load_data()
        else:
            data = reader.read(group_name="Zdata", func=reader.read_array)
            self.set_data(data)
        self.set_lut_range(lut_range)
        self.setZ(reader.read("z"))
        self.param = self.get_default_param()
        reader.read("imageparam", instance=self.param)
        self.param.update_item(self)

    # ---- Public API ----------------------------------------------------------
    def load_data(self, lut_range=None):
        """
        Load data from *filename* and eventually apply specified lut_range
        *filename* has been set using method 'set_filename'
        """
        data = io.imread(self.get_filename(), to_grayscale=True)
        self.set_data(data, lut_range=lut_range)

    def set_data(self, data, lut_range=None):
        """
        Set Image item data

            * data: 2D NumPy array
            * lut_range: LUT range -- tuple (levelmin, levelmax)
        """
        if lut_range is not None:
            _min, _max = lut_range
        else:
            _min, _max = _nanmin(data), _nanmax(data)

        self.data = data
        self.histogram_cache = None
        self.update_bounds()
        self.update_border()
        self.set_lut_range([_min, _max])

    def update_bounds(self):
        """

        :return:
        """
        if self.data is None:
            return
        self.bounds = QC.QRectF(0, 0, self.data.shape[1], self.data.shape[0])

    # ---- IBasePlotItem API ---------------------------------------------------
    def types(self):
        """

        :return:
        """
        return (
            IImageItemType,
            IVoiImageItemType,
            IColormapImageItemType,
            ITrackableItemType,
            ICSImageItemType,
            ISerializableType,
            IExportROIImageItemType,
            IStatsImageItemType,
        )

    def update_item_parameters(self):
        """ """
        self.param.update_param(self)

    def get_item_parameters(self, itemparams):
        """

        :param itemparams:
        """
        BaseImageItem.get_item_parameters(self, itemparams)
        self.update_item_parameters()
        itemparams.add("ImageParam", self, self.param)

    def set_item_parameters(self, itemparams):
        """

        :param itemparams:
        """
        update_dataset(self.param, itemparams.get("ImageParam"), visible_only=True)
        self.param.update_item(self)
        BaseImageItem.set_item_parameters(self, itemparams)

    # ---- IBaseImageItem API --------------------------------------------------
    def can_setfullscale(self):
        """

        :return:
        """
        return True

    def can_sethistogram(self):
        """

        :return:
        """
        return True


assert_interfaces_valid(RawImageItem)
