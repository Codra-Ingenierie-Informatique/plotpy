# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from qtpy import QtCore as QC

from plotpy._scaler import INTERP_NEAREST, _scale_rect, _scale_xy
from plotpy.config import _
from plotpy.interfaces.common import (
    IBaseImageItem,
    IBasePlotItem,
    IHistDataSource,
    IVoiImageItemType,
)
from plotpy.items.image.image_items import ImageItem, XYImageItem
from plotpy.items.image.masked_area import MaskedArea
from plotpy.items.image.mixin import MaskedImageMixin
from plotpy.styles.image import MaskedImageParam, MaskedXYImageParam

if TYPE_CHECKING:  # pragma: no cover
    import guidata.dataset.io
    import qwt.scale_map
    from qtpy.QtCore import QRectF
    from qtpy.QtGui import QPainter


class MaskedImageItem(ImageItem, MaskedImageMixin):
    """Masked image item

    Args:
        data: 2D NumPy array
        mask: 2D NumPy array
        param: image parameters
    """

    __implements__ = (IBasePlotItem, IBaseImageItem, IHistDataSource, IVoiImageItemType)

    def __init__(
        self,
        data: np.ndarray | None = None,
        mask: np.ndarray | None = None,
        param: MaskedImageParam | None = None,
    ) -> None:
        self.orig_data = None
        MaskedImageMixin.__init__(self, mask=mask)
        ImageItem.__init__(self, data=data, param=param)

    # ---- BaseImageItem API ---------------------------------------------------
    def get_default_param(self) -> MaskedImageParam:
        """Return instance of the default MaskedImageParam DataSet"""
        return MaskedImageParam(_("Image"))

    # ---- Pickle methods -------------------------------------------------------
    def __reduce__(self) -> tuple:
        """Reduce object to pickled state"""
        fname = self.get_filename()
        if fname is None:
            fn_or_data = self.data
        else:
            fn_or_data = fname
        state = (
            self.param,
            self.get_lut_range(),
            fn_or_data,
            self.z(),
            self.get_mask_filename(),
            self.get_masked_areas(),
        )
        res = (self.__class__, (), state)
        return res

    def __setstate__(self, state: tuple) -> None:
        """Set object state from pickled state"""
        param, lut_range, fn_or_data, z, mask_fname, old_masked_areas = state
        if old_masked_areas and isinstance(old_masked_areas[0], MaskedArea):
            masked_areas = old_masked_areas
        else:
            # Compatibility with old format
            masked_areas = []
            for geometry, x0, y0, x1, y1, inside in old_masked_areas:
                area = MaskedArea(
                    geometry=geometry, x0=x0, y0=y0, x1=x1, y1=y1, inside=inside
                )
                masked_areas.append(area)
        self.param = param
        if isinstance(fn_or_data, str):
            self.set_filename(fn_or_data)
            self.load_data(lut_range)
        elif fn_or_data is not None:  # should happen only with previous API
            self.set_data(fn_or_data, lut_range=lut_range)
        self.setZ(z)
        self.param.update_item(self)
        if mask_fname is not None:
            self.set_mask_filename(mask_fname)
            self.load_mask_data()
        elif masked_areas and self.data is not None:
            self.set_masked_areas(masked_areas)
            self.apply_masked_areas()

    def serialize(
        self,
        writer: guidata.dataset.io.HDF5Writer
        | guidata.dataset.io.INIWriter
        | guidata.dataset.io.JSONWriter,
    ) -> None:
        """Serialize object to HDF5 writer

        Args:
            writer: HDF5, INI or JSON writer
        """
        ImageItem.serialize(self, writer)
        MaskedImageMixin.serialize(self, writer)

    def deserialize(
        self,
        reader: guidata.dataset.io.HDF5Reader
        | guidata.dataset.io.INIReader
        | guidata.dataset.io.JSONReader,
    ) -> None:
        """Deserialize object from HDF5 reader

        Args:
            reader: HDF5, INI or JSON reader
        """
        ImageItem.deserialize(self, reader)
        MaskedImageMixin.deserialize(self, reader)

    # ---- BaseImageItem API ----------------------------------------------------
    def draw_image(
        self,
        painter: QPainter,
        canvasRect: QRectF,
        src_rect: tuple[float, float, float, float],
        dst_rect: tuple[float, float, float, float],
        xMap: qwt.scale_map.QwtScaleMap,
        yMap: qwt.scale_map.QwtScaleMap,
    ) -> None:
        """Draw image

        Args:
            painter: Painter
            canvasRect: Canvas rectangle
            src_rect: Source rectangle
            dst_rect: Destination rectangle
            xMap: X axis scale map
            yMap: Y axis scale map
        """
        ImageItem.draw_image(self, painter, canvasRect, src_rect, dst_rect, xMap, yMap)
        if self.data is None:
            return
        if self.is_mask_visible():
            _a, _b, bg, _cmap = self.lut
            # pylint: disable=too-many-function-args
            alpha_masked = (
                np.uint32(255 * self.param.alpha_masked + 0.5).clip(0, 255) << 24
            )
            alpha_unmasked = (
                np.uint32(255 * self.param.alpha_unmasked + 0.5).clip(0, 255) << 24
            )
            cmap = np.array(
                [
                    np.uint32(0x000000 & 0xFFFFFF) | alpha_unmasked,
                    np.uint32(0xFFFFFF & 0xFFFFFF) | alpha_masked,
                ],
                dtype=np.uint32,
            )
            lut = (1, 0, bg, cmap)
            shown_data = np.ma.getmaskarray(self.data)
            src2 = self._rescale_src_rect(src_rect)
            dst_rect = tuple([int(i) for i in dst_rect])
            dest = _scale_rect(
                shown_data, src2, self._offscreen, dst_rect, lut, (INTERP_NEAREST,)
            )
            qrect = QC.QRectF(
                QC.QPointF(dest[0], dest[1]), QC.QPointF(dest[2], dest[3])
            )
            painter.drawImage(qrect, self._image, qrect)

    # ---- RawImageItem API -----------------------------------------------------
    def set_data(
        self, data: np.ndarray, lut_range: list[float, float] | None = None
    ) -> None:
        """Set image data

        Args:
            data: 2D NumPy array
            lut_range: LUT range -- tuple (levelmin, levelmax) (Default value = None)
        """
        super().set_data(data, lut_range)
        MaskedImageMixin._set_data(self, data)


class MaskedXYImageItem(XYImageItem, MaskedImageMixin):
    """XY masked image item

    Args:
        x: 1D NumPy array, must be increasing
        y: 1D NumPy array, must be increasing
        data: 2D NumPy array
        mask: 2D NumPy array
        param: image parameters
    """

    __implements__ = (IBasePlotItem, IBaseImageItem, IHistDataSource, IVoiImageItemType)

    def __init__(
        self,
        x: np.ndarray | None = None,
        y: np.ndarray | None = None,
        data: np.ndarray | None = None,
        mask: np.ndarray | None = None,
        param: MaskedXYImageParam | None = None,
    ) -> None:
        self.orig_data = None
        MaskedImageMixin.__init__(self, mask=mask)
        XYImageItem.__init__(self, x=x, y=y, data=data, param=param)

    # ---- BaseImageItem API ---------------------------------------------------
    def get_default_param(self) -> MaskedXYImageParam:
        """Return instance of the default MaskedXYImageParam DataSet"""
        return MaskedXYImageParam(_("Image"))

    # ---- Pickle methods -------------------------------------------------------
    def __reduce__(self) -> tuple:
        """Reduce object to pickled state"""
        fname = self.get_filename()
        if fname is None:
            fn_or_data = self.data
        else:
            fn_or_data = fname
        state = (
            self.param,
            self.get_lut_range(),
            fn_or_data,
            self.x,
            self.y,
            self.z(),
            self.get_mask_filename(),
            self.get_masked_areas(),
        )
        res = (self.__class__, (), state)
        return res

    def __setstate__(self, state: tuple) -> None:
        """Set object state from pickled state"""
        param, lut_range, fn_or_data, x, y, z, mask_fname, old_masked_areas = state
        if old_masked_areas and isinstance(old_masked_areas[0], MaskedArea):
            masked_areas = old_masked_areas
        else:
            # Compatibility with old format
            masked_areas = []
            for geometry, x0, y0, x1, y1, inside in old_masked_areas:
                area = MaskedArea(
                    geometry=geometry, x0=x0, y0=y0, x1=x1, y1=y1, inside=inside
                )
                masked_areas.append(area)
        self.param = param
        if isinstance(fn_or_data, str):
            self.set_filename(fn_or_data)
            self.load_data(lut_range)
        elif fn_or_data is not None:  # should happen only with previous API
            self.set_data(fn_or_data, lut_range=lut_range)
        self.set_xy(x, y)
        self.setZ(z)
        self.param.update_item(self)
        self.set_transform(*self.get_transform())
        if mask_fname is not None:
            self.set_mask_filename(mask_fname)
            self.load_mask_data()
        elif masked_areas and self.data is not None:
            self.set_masked_areas(masked_areas)
            self.apply_masked_areas()

    def serialize(
        self,
        writer: guidata.dataset.io.HDF5Writer
        | guidata.dataset.io.INIWriter
        | guidata.dataset.io.JSONWriter,
    ) -> None:
        """Serialize object to HDF5 writer

        Args:
            writer: HDF5, INI or JSON writer
        """
        XYImageItem.serialize(self, writer)
        MaskedImageMixin.serialize(self, writer)

    def deserialize(
        self,
        reader: guidata.dataset.io.HDF5Reader
        | guidata.dataset.io.INIReader
        | guidata.dataset.io.JSONReader,
    ) -> None:
        """Deserialize object from HDF5 reader

        Args:
            reader: HDF5, INI or JSON reader
        """
        XYImageItem.deserialize(self, reader)
        MaskedImageMixin.deserialize(self, reader)

    # ---- BaseImageItem API ----------------------------------------------------
    def draw_image(
        self,
        painter: QPainter,
        canvasRect: QRectF,
        src_rect: tuple[float, float, float, float],
        dst_rect: tuple[float, float, float, float],
        xMap: qwt.scale_map.QwtScaleMap,
        yMap: qwt.scale_map.QwtScaleMap,
    ) -> None:
        """Draw image

        Args:
            painter: Painter
            canvasRect: Canvas rectangle
            src_rect: Source rectangle
            dst_rect: Destination rectangle
            xMap: X axis scale map
            yMap: Y axis scale map
        """
        XYImageItem.draw_image(
            self, painter, canvasRect, src_rect, dst_rect, xMap, yMap
        )
        if self.data is None:
            return
        if self.is_mask_visible():
            _a, _b, bg, _cmap = self.lut
            # pylint: disable=too-many-function-args
            alpha_masked = (
                np.uint32(255 * self.param.alpha_masked + 0.5).clip(0, 255) << 24
            )
            alpha_unmasked = (
                np.uint32(255 * self.param.alpha_unmasked + 0.5).clip(0, 255) << 24
            )
            cmap = np.array(
                [
                    np.uint32(0x000000 & 0xFFFFFF) | alpha_unmasked,
                    np.uint32(0xFFFFFF & 0xFFFFFF) | alpha_masked,
                ],
                dtype=np.uint32,
            )
            lut = (1, 0, bg, cmap)
            shown_data = np.ma.getmaskarray(self.data)

            W = canvasRect.width()
            H = canvasRect.height()
            if W <= 1 or H <= 1:
                return

            x0, y0, x1, y1 = src_rect
            cx = canvasRect.left()
            cy = canvasRect.top()
            sx = (x1 - x0) / (W - 1)
            sy = (y1 - y0) / (H - 1)
            # tr1 = tr(x0,y0)*scale(sx,sy)*tr(-cx,-cy)
            tr = np.matrix(
                [[sx, 0, x0 - cx * sx], [0, sy, y0 - cy * sy], [0, 0, 1]], float
            )
            mat = self.tr * tr

            xytr = self.x, self.y, src_rect
            dst_rect = tuple([int(i) for i in dst_rect])
            dest = _scale_xy(
                shown_data, xytr, mat, self._offscreen, dst_rect, lut, (INTERP_NEAREST,)
            )
            qrect = QC.QRectF(
                QC.QPointF(dest[0], dest[1]), QC.QPointF(dest[2], dest[3])
            )
            painter.drawImage(qrect, self._image, qrect)

    def set_data(
        self, data: np.ndarray, lut_range: list[float, float] | None = None
    ) -> None:
        """Set image data

        Args:
            data: 2D NumPy array
            lut_range: LUT range -- tuple (levelmin, levelmax) (Default value = None)
        """
        super().set_data(data, lut_range)
        MaskedImageMixin._set_data(self, data)
