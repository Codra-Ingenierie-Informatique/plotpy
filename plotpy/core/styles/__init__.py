# Copyright CEA (2018)

# http://www.cea.fr/

# This software is a computer program whose purpose is to provide an
# Automatic GUI generation for easy dataset editing and display with
# Python.

# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info".

# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.

# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.

# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

"""
plotpy.core.styles
---------------------

The `styles` module provides set of parameters (DataSet classes) to
configure `plot items` and `plot tools`.

.. seealso::

    Module :py:mod:`.plot`
        Module providing ready-to-use curve and image plotting widgets and
        dialog boxes

    Module :py:mod:`.curve`
        Module providing curve-related plot items and plotting widgets

    Module :py:mod:`.image`
        Module providing image-related plot items and plotting widgets

    Module :py:mod:`.tools`
        Module providing the `plot tools`

Reference
~~~~~~~~~

.. autoclass:: CurveParam
   :members:
   :inherited-members:
.. autoclass:: ErrorBarParam
   :members:
   :inherited-members:
.. autoclass:: GridParam
   :members:
   :inherited-members:
.. autoclass:: ImageParam
   :members:
   :inherited-members:
.. autoclass:: TrImageParam
   :members:
   :inherited-members:
.. autoclass:: ImageFilterParam
   :members:
   :inherited-members:
.. autoclass:: HistogramParam
   :members:
   :inherited-members:
.. autoclass:: Histogram2DParam
   :members:
   :inherited-members:
.. autoclass:: AxesParam
   :members:
   :inherited-members:
.. autoclass:: ImageAxesParam
   :members:
   :inherited-members:
.. autoclass:: LabelParam
   :members:
   :inherited-members:
.. autoclass:: LegendParam
   :members:
   :inherited-members:
.. autoclass:: ShapeParam
   :members:
   :inherited-members:
.. autoclass:: AnnotationParam
   :members:
   :inherited-members:
.. autoclass:: AxesShapeParam
   :members:
   :inherited-members:
.. autoclass:: RangeShapeParam
   :members:
   :inherited-members:
.. autoclass:: MarkerParam
   :members:
   :inherited-members:
.. autoclass:: FontParam
   :members:
   :inherited-members:
.. autoclass:: SymbolParam
   :members:
   :inherited-members:
.. autoclass:: LineStyleParam
   :members:
   :inherited-members:
.. autoclass:: BrushStyleParam
   :members:
   :inherited-members:
.. autoclass:: TextStyleParam
   :members:
   :inherited-members:
.. autoclass:: RawImageParam
   :members:
   :inherited-members:
.. autoclass:: XYImageParam
   :members:
   :inherited-members:
.. autoclass:: RGBImageParam
   :members:
   :inherited-members:
.. autoclass:: MaskedImageParam
   :members:
   :inherited-members:
.. autoclass:: MaskedXYImageParam
   :members:
   :inherited-members:

"""
from plotpy.core.styles.axes import (
    AxesParam,
    AxeStyleParam,
    AxisItem,
    AxisItemWidget,
    AxisParam,
    ImageAxesParam,
)
from plotpy.core.styles.base import (
    BrushStyleItem,
    BrushStyleItemWidget,
    BrushStyleParam,
    FontItem,
    FontItemWidget,
    FontParam,
    GridParam,
    ItemParameters,
    LineStyleItem,
    LineStyleItemWidget,
    LineStyleParam,
    SymbolItem,
    SymbolItemWidget,
    SymbolParam,
    TextStyleItem,
    TextStyleItemWidget,
    TextStyleParam,
    style_generator,
    update_style_attr,
)
from plotpy.core.styles.curve import CurveParam, CurveParam_MS
from plotpy.core.styles.errorbar import ErrorBarParam
from plotpy.core.styles.histogram import (
    Histogram2DParam,
    Histogram2DParam_MS,
    HistogramParam,
)
from plotpy.core.styles.image import (
    BaseImageParam,
    ImageFilterParam,
    ImageParam,
    ImageParam_MS,
    ImageParamMixin,
    MaskedImageParam,
    MaskedImageParam_MS,
    MaskedImageParamMixin,
    MaskedXYImageParam,
    MaskedXYImageParam_MS,
    QuadGridParam,
    RawImageParam,
    RawImageParam_MS,
    RGBImageParam,
    TransformParamMixin,
    TrImageParam,
    TrImageParam_MS,
    XYImageParam,
    XYImageParam_MS,
)
from plotpy.core.styles.label import (
    LabelParam,
    LabelParam_MS,
    LabelParamWithContents,
    LabelParamWithContents_MS,
    LegendParam,
    LegendParam_MS,
)
from plotpy.core.styles.shape import (
    AnnotationParam,
    AnnotationParam_MS,
    AxesShapeParam,
    MarkerParam,
    RangeShapeParam,
    ShapeParam,
)
