# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see plotpy/LICENSE for details)


from copy import deepcopy

import qtpy.QtCore as QC
import qtpy.QtGui as QG
import qtpy.QtWidgets as QW
from guidata.config import _
from guidata.configtools import get_icon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget

from plotpy.mathutils.colormaps import (
    ALL_COLORMAPS,
    CUSTOM_COLORMAPS,
    CUSTOM_COLORMAPS_PATH,
    DEFAULT_COLORMAPS,
    build_icon_from_cmap,
    save_colormaps,
)
from plotpy.widgets.colormap_editor import ColorMapEditor
from plotpy.widgets.colormap_widget import CustomQwtLinearColormap


class ColorMapManager(QW.QWidget):
    """Wrapper around a ColorMapEditor to allow for selection, edition and save of
    of colormaps.

    Args:
        parent: parent QWidget. Defaults to None.
        active_colormap: name of the default colormap selected. If None or does not
        exists, will defaults to the first colormap in the list. Defaults to None
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        active_colormap: str | None = None,
    ) -> None:
        super().__init__(parent)

        self._vlayout = QW.QVBoxLayout()
        self._vlayout.setContentsMargins(0, 0, 0, 0)

        if active_colormap is None or active_colormap not in ALL_COLORMAPS:
            active_colormap = next(iter(ALL_COLORMAPS))

        self._cmap_choice = QW.QComboBox(
            self,
        )

        # Adding a default white colormap to the choices
        white_rgb = 4294967295
        new_colormap = CustomQwtLinearColormap(
            QG.QColor(white_rgb), QG.QColor(white_rgb), name="New"
        )
        icon = build_icon_from_cmap(new_colormap)
        self._cmap_choice.addItem(icon, new_colormap.name, new_colormap)

        for cmap_name, cmap in ALL_COLORMAPS.items():
            icon = build_icon_from_cmap(cmap)
            self._cmap_choice.addItem(icon, cmap_name, cmap)
        self._cmap_choice.setCurrentText(active_colormap)

        self._colormap_editor = ColorMapEditor(
            self, colormap=deepcopy(self._cmap_choice.currentData())
        )

        hlayout = QW.QHBoxLayout()
        hlayout.setAlignment(QC.Qt.AlignmentFlag.AlignRight)

        regex = QC.QRegExp("[1-9a-zA-Z_]*")
        validator = QG.QRegExpValidator(regex)
        self._colormap_name_edit = QW.QLineEdit(self)
        self._colormap_name_edit.setValidator(validator)
        self._colormap_name_edit.setPlaceholderText("Enter a new custom colomap filame")
        self._colormap_name_edit.setText(active_colormap)
        self._colormap_name_edit.setToolTip(
            _(
                "New colormap name cannot contain special characters except underscores (_)."
            )
        )
        self._colormap_name_edit.setEnabled(False)

        self._changes_saved = True
        self._save_btn = QW.QPushButton(self)
        self._save_btn.setMaximumWidth(50)
        self._save_btn.setIcon(get_icon("filesave.png"))
        self._save_btn.setEnabled(False)

        hlayout.addWidget(self._cmap_choice)
        hlayout.addWidget(self._colormap_name_edit)
        hlayout.addWidget(self._save_btn)

        # self._vlayout.addWidget(self._cmap_choice)
        self._vlayout.addLayout(hlayout)

        groupbox = QW.QGroupBox(_("Editor"), self)
        groupbox_layout = QW.QVBoxLayout()
        groupbox_layout.setContentsMargins(0, 0, 0, 0)
        groupbox_layout.addWidget(self._colormap_editor)
        groupbox.setLayout(groupbox_layout)
        self._vlayout.addWidget(groupbox)
        # self._vlayout.addWidget(self._colormap_editor)

        self._colormap_editor.colormap_widget.colormapChanged.connect(
            self._changes_not_saved
        )
        self._cmap_choice.currentIndexChanged.connect(self.setColormap)
        self._save_btn.clicked.connect(self.saveColormap)
        self._colormap_name_edit.editingFinished.connect(self.update_colormap_name)
        self.setLayout(self._vlayout)

    def _changes_not_saved(self):
        self._colormap_name_edit.setEnabled(True)
        self._save_btn.setEnabled(True)
        self._changes_saved = False

    @property
    def current_changes_saved(self):
        return self._changes_saved

    def update_colormap_name(self):
        self.getColormap().name = self._colormap_name_edit.text()

    def setColormap(self, index: int):
        """Set the current colormap to the value present at the given index in the
        QComboBox. Makes a copy of the colormap object so the ColorMapEditor does not
        mutate the original colormap object.

        Args:
            index: index of the colormap in the QComboBox.
        """
        cmap_copy: CustomQwtLinearColormap = deepcopy(self._cmap_choice.itemData(index))
        self._colormap_editor.setColormap(cmap_copy)
        self._colormap_name_edit.setText(cmap_copy.name)
        is_new_colormap = cmap_copy.name not in ALL_COLORMAPS
        self._colormap_name_edit.setEnabled(is_new_colormap)
        self._changes_saved = True
        self._save_btn.setEnabled(is_new_colormap)

    def getColormap(self):
        """Return the current colormap object.

        Returns:
            current colormap object
        """
        return self._colormap_editor.getColormap()

    def saveColormap(self):
        """Saves the current colormap and handles the validation process. The saved
        colormaps can only be saved in the custom colormaps.
        """
        cmap = self.getColormap()
        new_cmap_name = cmap.name

        if new_cmap_name not in DEFAULT_COLORMAPS:
            is_cmap_in_default = new_cmap_name in CUSTOM_COLORMAPS
            if is_cmap_in_default and not self.show_validation_modal(
                _("Custom colormap %s already exists, do you want to overwrite it?")
                % new_cmap_name
            ):
                return
            icon = build_icon_from_cmap(cmap)
            CUSTOM_COLORMAPS[new_cmap_name] = ALL_COLORMAPS[new_cmap_name] = cmap
            save_colormaps(CUSTOM_COLORMAPS_PATH, CUSTOM_COLORMAPS)
            if is_cmap_in_default:
                self._cmap_choice.setCurrentText(new_cmap_name)
                current_index = self._cmap_choice.currentIndex()
                self._cmap_choice.setItemData(current_index, cmap)
                self._cmap_choice.setItemIcon(current_index, icon)
            else:
                self._cmap_choice.addItem(icon, new_cmap_name, cmap)
                self._cmap_choice.setCurrentText(new_cmap_name)
            self._colormap_name_edit.setEnabled(False)
            self._save_btn.setEnabled(False)
            self._changes_saved = True
        else:
            QW.QMessageBox.critical(
                self,
                "Colormap map error",
                _(
                    'New colormap "%s" is a default colormap and cannot be overwritten. Change its name to save it as a custom colormap.'
                )
                % new_cmap_name,
            )

    def show_validation_modal(
        self,
        message: str,
        validation_btn: QW.QMessageBox.StandardButton = QW.QMessageBox.StandardButton.Ok,
    ):
        """Opens a simple QMessageBox with the given message and validation button

        Args:
            message: message to display
            validation_btn: validation button. Defaults to QW.QMessageBox.StandardButton.Ok.

        Returns:
            _description_
        """
        ret = QW.QMessageBox.question(self, "Validation", message, validation_btn | QW.QMessageBox.StandardButton.Cancel, QW.QMessageBox.StandardButton.Cancel)  # type: ignore
        return ret == validation_btn


class ColorMapManagerDialog(QW.QDialog):
    """Wrapper around the ColorMapManager to open it in its own dialog box.

    Args:
        parent: parent QWidget. Defaults to None.
        active_colormap: name of the default colormap selected. If None or does not
        exists, will defaults to the first colormap in the list. Defaults to None
    """

    def __init__(
        self, parent: QWidget | None, active_colormap: str = "viridis"
    ) -> None:
        super().__init__(parent)
        self.setWindowIcon(get_icon("edit.png"))
        self.setWindowTitle(_("Colormap manager"))
        self._layout = QW.QVBoxLayout()
        self.cmap_manager = ColorMapManager(self, active_colormap)
        self.btn_close = QW.QPushButton(_("Close"))
        self._layout.addWidget(self.cmap_manager)
        self._layout.addWidget(self.btn_close, alignment=QC.Qt.AlignmentFlag.AlignRight)
        self.setLayout(self._layout)
        self.btn_close.clicked.connect(self.check_save_before_close)

    def check_save_before_close(self):
        """Adds logic on top of the normal QDialog.close method to handle colormap save."""
        if not self.cmap_manager.current_changes_saved:
            save = self.cmap_manager.show_validation_modal(
                _(
                    "Current changes not saved. "
                    "The current colormap will be discarded when the editor is closed.\n"
                    "Do you want to save the changes?"
                ),
                QW.QMessageBox.StandardButton.Save,
            )
            if save:
                self.cmap_manager.saveColormap()

        if self.cmap_manager.current_changes_saved:
            self.close()

    def show(self) -> None:
        return super().show()

    def getColormap(self):
        return self.cmap_manager.getColormap()
