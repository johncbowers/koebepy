"""Control-panel helpers for interactive Qt sketches."""

from __future__ import absolute_import

import builtins
from decimal import Decimal
import numbers

from ._qt import require_qt


_QtCore, _QtGui, _QtWidgets = require_qt()


class _ElidedLabel(_QtWidgets.QLabel):
    """QLabel that elides long text instead of changing layout width."""

    def __init__(self, text="", parent=None):
        _QtWidgets.QLabel.__init__(self, parent)
        self._full_text = ""
        self.setWordWrap(False)
        self.setText(text)

    def setText(self, text):
        self._full_text = str(text)
        self._update_elided_text()

    def text(self):
        return self._full_text

    def resizeEvent(self, event):
        _QtWidgets.QLabel.resizeEvent(self, event)
        self._update_elided_text()

    def _update_elided_text(self):
        metrics = self.fontMetrics()
        available_width = max(0, self.contentsRect().width())
        if available_width <= 0:
            display_text = self._full_text
        else:
            display_text = metrics.elidedText(
                self._full_text,
                _QtCore.Qt.ElideRight,
                available_width,
            )
        _QtWidgets.QLabel.setText(self, display_text)


class BaseControl(object):
    """Small wrapper around an underlying Qt widget."""

    def __init__(self, widget):
        self._widget = widget

    @property
    def widget(self):
        return self._widget


class ButtonControl(BaseControl):
    pass


class CheckboxControl(BaseControl):
    def is_checked(self):
        return bool(self._widget.isChecked())

    def set_checked(self, checked):
        self._widget.setChecked(bool(checked))


class NumberFieldControl(BaseControl):
    def value(self):
        return self._widget.value()

    def set_value(self, value):
        self._widget.setValue(value)


class SliderControl(BaseControl):
    def __init__(self, widget, value_label, to_python, to_qt):
        BaseControl.__init__(self, widget)
        self._value_label = value_label
        self._to_python = to_python
        self._to_qt = to_qt

    def value(self):
        return self._to_python(self._widget.value())

    def set_value(self, value):
        self._widget.setValue(self._to_qt(value))
        self._value_label.setText(str(self.value()))

    def set_text(self, text):
        self._value_label.setText(text)


class TextControl(BaseControl):
    def set_text(self, text):
        self._widget.setText(str(text))
        self._widget.setToolTip(str(text))

    def text(self):
        return self._widget.text()


class ControlPanel(object):
    """A vertical container of native Qt controls."""

    DEFAULT_MINIMUM_WIDTH = 280

    def __init__(self, title="", parent=None, width=None):
        _QtCore, _QtGui, QtWidgets = require_qt()
        self._QtWidgets = QtWidgets
        self._group = QtWidgets.QGroupBox(title, parent)
        self._width = self.DEFAULT_MINIMUM_WIDTH if width is None else int(width)
        self._group.setMinimumWidth(self._width)
        self._group.setMaximumWidth(self._width)
        self._group.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed,
            QtWidgets.QSizePolicy.Preferred,
        )
        self._layout = QtWidgets.QVBoxLayout(self._group)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(6)
        self._layout.addStretch(1)

    @property
    def widget(self):
        return self._group

    @property
    def width(self):
        return self._width

    def add_button(self, text, on_click=None):
        button = self._QtWidgets.QPushButton(text, self._group)
        if on_click is not None:
            button.clicked.connect(lambda _checked=False: on_click())
        self._insert_widget(button)
        return ButtonControl(button)

    def add_checkbox(self, text, checked=False, on_change=None):
        checkbox = self._QtWidgets.QCheckBox(text, self._group)
        checkbox.setChecked(bool(checked))
        if on_change is not None:
            checkbox.toggled.connect(on_change)
        self._insert_widget(checkbox)
        return CheckboxControl(checkbox)

    def add_number_field(self, name, value=0, on_change=None, minimum=None, maximum=None, decimals=6):
        row = self._QtWidgets.QWidget(self._group)
        layout = self._QtWidgets.QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        label = self._QtWidgets.QLabel(name, row)
        layout.addWidget(label)

        if isinstance(value, numbers.Integral):
            field = self._QtWidgets.QSpinBox(row)
            if minimum is not None:
                field.setMinimum(int(minimum))
            if maximum is not None:
                field.setMaximum(int(maximum))
        else:
            field = self._QtWidgets.QDoubleSpinBox(row)
            field.setDecimals(int(decimals))
            if minimum is not None:
                field.setMinimum(float(minimum))
            if maximum is not None:
                field.setMaximum(float(maximum))
        field.setValue(value)
        if on_change is not None:
            field.valueChanged.connect(on_change)
        layout.addWidget(field, 1)
        self._insert_widget(row)
        return NumberFieldControl(field)

    def add_slider(self, name, min=0, max=100, value=0, step=None, on_change=None):
        QtCore, _QtGui, _QtWidgets = require_qt()
        row = self._QtWidgets.QWidget(self._group)
        layout = self._QtWidgets.QVBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)

        title_layout = self._QtWidgets.QHBoxLayout()
        name_label = self._QtWidgets.QLabel(name, row)
        value_label = self._QtWidgets.QLabel(row)
        title_layout.addWidget(name_label)
        title_layout.addStretch(1)
        title_layout.addWidget(value_label)
        layout.addLayout(title_layout)

        slider = self._QtWidgets.QSlider(QtCore.Qt.Horizontal, row)
        slider.setTracking(True)

        scale = self._slider_scale(step)
        slider_min = int(round(float(min) * scale))
        slider_max = int(round(float(max) * scale))
        slider.setMinimum(slider_min)
        slider.setMaximum(slider_max)
        slider.setSingleStep(
            builtins.max(1, int(round(float(step if step is not None else 1) * scale)))
        )
        slider.setValue(int(round(float(value) * scale)))

        def to_qt(python_value):
            clamped = builtins.min(
                builtins.max(float(python_value), float(min)),
                float(max),
            )
            return int(round(clamped * scale))

        def to_python(raw_value):
            converted = float(raw_value) / float(scale)
            if self._all_integral(min, max, value, step):
                return int(round(converted))
            return converted

        value_label.setText(str(to_python(slider.value())))

        if on_change is not None:
            def emit(raw_value):
                converted = to_python(raw_value)
                value_label.setText(str(converted))
                on_change(converted)
            slider.valueChanged.connect(emit)
        else:
            slider.valueChanged.connect(lambda raw_value: value_label.setText(str(to_python(raw_value))))

        layout.addWidget(slider)
        self._insert_widget(row)
        return SliderControl(slider, value_label, to_python, to_qt)

    def add_text(self, name, text):
        row = self._QtWidgets.QWidget(self._group)
        layout = self._QtWidgets.QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        name_label = self._QtWidgets.QLabel(name, row)
        value_label = _ElidedLabel(str(text), row)
        value_label.setSizePolicy(
            self._QtWidgets.QSizePolicy.Expanding,
            self._QtWidgets.QSizePolicy.Preferred,
        )
        value_label.setToolTip(str(text))
        layout.addWidget(name_label)
        layout.addWidget(value_label, 1)
        self._insert_widget(row)
        return TextControl(value_label)

    def _insert_widget(self, widget):
        self._layout.insertWidget(self._layout.count() - 1, widget)

    @staticmethod
    def _all_integral(*values):
        filtered = [value for value in values if value is not None]
        return all(isinstance(value, numbers.Integral) for value in filtered)

    @staticmethod
    def _slider_scale(step):
        if step is None:
            return 1
        decimal_step = Decimal(str(step)).normalize()
        exponent = decimal_step.as_tuple().exponent
        return 10 ** max(0, -exponent)
