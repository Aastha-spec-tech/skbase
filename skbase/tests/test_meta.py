# -*- coding: utf-8 -*-
# copyright: skbase developers, BSD-3-Clause License (see LICENSE file)
"""Tests for BaseMetaObject and BaseMetaEstimator mixins."""

__author__ = ["RNKuhns", "fkiraly"]
import inspect

import pytest

from skbase._exceptions import NotFittedError
from skbase.base import BaseEstimator, BaseObject
from skbase.base._meta import (
    BaseMetaEstimator,
    BaseMetaObject,
    _MetaObjectMixin,
    _MetaTagLogicMixin,
)
from skbase.base._tagmanager import _FlagManager


class MetaObjectTester(BaseMetaObject):
    """Class to test meta-object functionality."""

    def __init__(self, a=7, b="something", c=None, steps=None):
        self.a = a
        self.b = b
        self.c = c
        self.steps = steps
        super().__init__()


class MetaEstimatorTester(BaseMetaEstimator):
    """Class to test meta-estimator functionality."""

    def __init__(self, a=7, b="something", c=None, steps=None):
        self.a = a
        self.b = b
        self.c = c
        self.steps = steps
        super().__init__()


class ComponentDummy(BaseObject):
    """Class to use as components in meta-estimator."""

    def __init__(self, a=7, b="something"):
        self.a = a
        self.b = b
        super().__init__()


@pytest.fixture
def fixture_metaestimator_instance():
    """BaseMetaEstimator instance fixture."""
    return BaseMetaEstimator()


@pytest.fixture
def fixture_meta_object():
    """MetaObjectTester instance fixture."""
    return MetaObjectTester()


@pytest.fixture
def fixture_meta_estimator():
    """MetaEstimatorTester instance fixture."""
    return MetaEstimatorTester()


def test_is_composite_returns_true(fixture_meta_object, fixture_meta_estimator):
    """Test that `is_composite` method returns True."""
    msg = "`is_composite` should always be True for subclasses of "
    assert fixture_meta_object.is_composite() is True, msg + "`BaseMetaObject`."
    assert fixture_meta_estimator.is_composite() is True, msg + "`BaseMetaEstimator`."


def test_basemetaestimator_inheritance(fixture_metaestimator_instance):
    """Check BaseMetaEstimator correctly inherits from BaseEstimator and BaseObject."""
    estimator_is_subclass_of_baseobejct = issubclass(BaseMetaEstimator, BaseObject)
    estimator_instance_is_baseobject_instance = isinstance(
        fixture_metaestimator_instance, BaseObject
    )

    # Verify that BaseMetaEstimator is an estimator
    assert (
        estimator_is_subclass_of_baseobejct
        and estimator_instance_is_baseobject_instance
    ), "`BaseMetaEstimator` not correctly subclassing `BaseEstimator` and `BaseObject`."

    # Verify expected MRO inheritance order
    mro_filtered = tuple(c for c in BaseMetaEstimator.__mro__ if c is not object)
    assert mro_filtered == (
        BaseMetaEstimator,
        _MetaObjectMixin,
        _MetaTagLogicMixin,
        BaseEstimator,
        BaseObject,
        _FlagManager,
    ), "`BaseMetaEstimator` has incorrect mro."


def test_basemetaestimator_has_is_fitted(fixture_metaestimator_instance):
    """Test BaseEstimator has `is_fitted` property."""
    has_private_is_fitted = hasattr(fixture_metaestimator_instance, "_is_fitted")
    has_is_fitted = hasattr(fixture_metaestimator_instance, "is_fitted")
    assert (
        has_private_is_fitted and has_is_fitted
    ), "`BaseMetaEstimator` does not have `is_fitted` property or `_is_fitted` attr."


def test_basemetaestimator_has_check_is_fitted(fixture_metaestimator_instance):
    """Test BaseEstimator has `check_is_fitted` method."""
    has_check_is_fitted = hasattr(fixture_metaestimator_instance, "check_is_fitted")
    is_method = inspect.ismethod(fixture_metaestimator_instance.check_is_fitted)
    assert (
        has_check_is_fitted and is_method
    ), "`BaseMetaEstimator` does not have `check_is_fitted` method."


@pytest.mark.parametrize("is_fitted_value", (True, False))
def test_basemetaestimator_is_fitted(fixture_metaestimator_instance, is_fitted_value):
    """Test BaseEstimator `is_fitted` property returns expected value."""
    fixture_metaestimator_instance._is_fitted = is_fitted_value
    expected_value_unfitted = (
        fixture_metaestimator_instance.is_fitted
        == fixture_metaestimator_instance._is_fitted
    )
    assert (
        expected_value_unfitted
    ), "`BaseMetaEstimator` property `is_fitted` does not return `_is_fitted` value."


def test_basemetaestimator_check_is_fitted_raises_error_when_unfitted(
    fixture_metaestimator_instance,
):
    """Test BaseEstimator `check_is_fitted` method raises an error."""
    name = fixture_metaestimator_instance.__class__.__name__
    match = f"This instance of {name} has not been fitted yet. Please call `fit` first."
    with pytest.raises(NotFittedError, match=match):
        fixture_metaestimator_instance.check_is_fitted()

    fixture_metaestimator_instance._is_fitted = True
    assert fixture_metaestimator_instance.check_is_fitted() is None


@pytest.mark.parametrize("long_steps", (True, False))
def test_metaestimator_composite(long_steps):
    """Test composite meta-estimator functionality."""
    if long_steps:
        steps = [("foo", ComponentDummy(42)), ("bar", ComponentDummy(24))]
    else:
        steps = [("foo", ComponentDummy(42), 123), ("bar", ComponentDummy(24), 321)]

    meta_est = MetaEstimatorTester(steps=steps)

    meta_est_params = meta_est.get_params()
    assert isinstance(meta_est_params, dict)
    expected_keys = [
        "a",
        "b",
        "c",
        "steps",
        "foo",
        "bar",
        "foo__a",
        "foo__b",
        "bar__a",
        "bar__b",
    ]
    assert set(meta_est_params.keys()) == set(expected_keys)

    meta_est.set_params(bar__b="something else")
    assert meta_est.get_params()["bar__b"] == "something else"


def test_check_objects_attr_name_auto_detection():
    """Test that _check_objects auto-detects attr_name from tag."""

    steps = [ComponentDummy(42), ComponentDummy(24)]
    meta_obj = MetaObjectTester(steps=steps)

    # auto-detect from tag
    result = meta_obj._check_objects(steps, attr_name=None)

    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(item, tuple) and len(item) == 2 for item in result)
    assert all(isinstance(item[0], str) for item in result)
    assert all(isinstance(item[1], ComponentDummy) for item in result)

    with pytest.raises(TypeError, match="'steps'"):
        meta_obj._check_objects(None, attr_name=None)


def test_check_objects_attr_name_explicit():
    """Test that _check_objects works with explicit attr_name."""
    # Create a meta object with steps
    steps = [ComponentDummy(42), ComponentDummy(24)]
    meta_obj = MetaObjectTester(steps=steps)

    # Test with explicit attr_name
    result = meta_obj._check_objects(steps, attr_name="custom_steps")

    assert isinstance(result, list)
    assert len(result) == 2

    with pytest.raises(TypeError, match="'custom_steps'"):
        meta_obj._check_objects(None, attr_name="custom_steps")


def test_check_objects_attr_name_custom_tag():
    """Test that _check_objects auto-detects from custom named_object_parameters tag."""
    # custom tag
    meta_obj = MetaObjectTester()
    meta_obj.set_tags(**{"named_object_parameters": "components"})

    components = [ComponentDummy(1), ComponentDummy(2)]

    # should auto-detect custom tag
    result = meta_obj._check_objects(components, attr_name=None)

    assert isinstance(result, list)
    assert len(result) == 2

    with pytest.raises(TypeError, match="'components'"):
        meta_obj._check_objects(None, attr_name=None)


def test_set_params_resets_fitted_state():
    """Test that set_params calls reset, removing fitted state.

    Regression test for issue #412.
    BaseMetaObject should call reset() during set_params() to clear fitted state,
    maintaining consistency with BaseObject behavior.
    """
    steps = [("foo", ComponentDummy(42)), ("bar", ComponentDummy(24))]
    meta_obj = MetaObjectTester(steps=steps)

    # Add some fitted state (simulating a fit operation)
    meta_obj.fitted_attr_ = "should be removed after set_params"
    meta_obj.another_fitted_ = 123

    # Test 1: Setting the named object parameter should trigger reset
    new_steps = [("foo", ComponentDummy(99))]
    meta_obj.set_params(steps=new_steps)

    # Fitted state should be gone after set_params
    assert not hasattr(
        meta_obj, "fitted_attr_"
    ), "fitted_attr_ should be removed by reset() during set_params(steps=...)"
    assert not hasattr(
        meta_obj, "another_fitted_"
    ), "another_fitted_ should be removed by reset() during set_params(steps=...)"

    # Test 2: Replacing individual step should also trigger reset
    meta_obj = MetaObjectTester(steps=steps)
    meta_obj.fitted_attr_ = "should be removed"

    meta_obj.set_params(foo=ComponentDummy(77))

    assert not hasattr(
        meta_obj, "fitted_attr_"
    ), "fitted_attr_ should be removed by reset() during set_params(foo=...)"


def test_get_class_flags_preserves_mixin_tags():
    """Regression test for Issue #539.

    `_get_class_flags` previously sliced the MRO with ``[:-2]``, assuming the
    last two entries are always ``BaseObject`` and ``object``.  Under multiple
    inheritance Python's C3 linearisation can place a user-defined Mixin class
    *after* ``BaseObject`` (i.e. at position -2), so the slice permanently
    dropped any flags defined on that Mixin.

    The fix iterates the full MRO and skips only ``object`` explicitly so that
    every user-defined class – regardless of its MRO position – contributes its
    flags.  This test pins that behaviour to prevent regressions.
    """

    class MyMixin:
        """Mixin that defines a tag.  Has no _FlagManager inheritance."""

        _flags = {"mixin_tag": 42}

    # Inheriting BaseObject *before* MyMixin forces MyMixin to the tail of the
    # MRO (just before `object`), which is exactly the scenario that was broken.
    class MyObj(BaseObject, MyMixin):
        """Concrete class using multiple inheritance."""

        _flags = {"own_tag": 1}

        def __init__(self):
            super().__init__()

    mro_classes = [c.__name__ for c in MyObj.__mro__]

    # Sanity-check: MyMixin should be near the tail (after BaseObject).
    assert mro_classes.index("MyMixin") > mro_classes.index(
        "BaseObject"
    ), "Test setup error: MyMixin should appear after BaseObject in the MRO."

    collected = MyObj._get_class_flags()

    # Both own_tag and mixin_tag must be present.
    assert (
        "own_tag" in collected
    ), "'own_tag' defined directly on MyObj was not collected."
    assert "mixin_tag" in collected, (
        "Regression (Issue #539): 'mixin_tag' from MyMixin was dropped by "
        "_get_class_flags.  The MRO slice [:-2] is being used again – revert "
        "to the explicit `if parent_class is object: continue` check."
    )
    assert collected["mixin_tag"] == 42
    assert collected["own_tag"] == 1


def test_check_objects_attr_name_none_tag_not_set():
    """Test error when attr_name is None and tag is not set or returns None."""
    meta_obj = MetaObjectTester()

    # Set tag to None explicitly
    meta_obj.set_tags(**{"named_object_parameters": None})

    steps = [ComponentDummy(1)]

    with pytest.raises(TypeError, match="could not be auto-detected.*non-empty string"):
        meta_obj._check_objects(steps, attr_name=None)


# Tests for _MetaTagLogicMixin
# ----------------------------
# The mixin methods take a list of (name, estimator) tuples and either query
# or set tags on the meta-object based on the tags of the components.


def _named_components(*tag_dicts):
    """Create list of (name, ComponentDummy) tuples with given dynamic tags."""
    return [
        (f"comp{i}", ComponentDummy().set_tags(**tags))
        for i, tags in enumerate(tag_dicts)
    ]


@pytest.fixture(params=[MetaObjectTester, MetaEstimatorTester])
def fixture_tag_logic_meta(request):
    """Meta-object instance inheriting _MetaTagLogicMixin, object and estimator."""
    return request.param()


@pytest.mark.parametrize(
    "tag_values, value, expected",
    [
        ([True, False, False], True, True),
        ([False, False, True], True, True),
        ([False, False, False], True, False),
        (["a", "b", "c"], "b", True),
        (["a", "b", "c"], "d", False),
        ([], True, False),
    ],
)
def test_anytagis(fixture_tag_logic_meta, tag_values, value, expected):
    """Test _anytagis returns whether any component has tag value."""
    estimators = _named_components(*[{"foo": v} for v in tag_values])

    result = fixture_tag_logic_meta._anytagis("foo", value, estimators)

    assert result is expected


@pytest.mark.parametrize(
    "tag_values, expected",
    [
        (["other", "yes"], "yes"),
        (["other", "other"], "no"),
    ],
)
def test_anytagis_then_set(fixture_tag_logic_meta, tag_values, expected):
    """Test _anytagis_then_set sets value if any component matches, else other."""
    estimators = _named_components(*[{"foo": v} for v in tag_values])

    fixture_tag_logic_meta._anytagis_then_set(
        "foo", value="yes", value_if_not="no", estimators=estimators
    )

    assert fixture_tag_logic_meta.get_tag("foo") == expected


@pytest.mark.parametrize(
    "tag_values, expected",
    [
        (["None", "None", "x", "y"], "x"),
        (["x", "None", "y"], "x"),
        ([42, "x"], 42),
        (["None", "None"], "None"),
    ],
)
def test_anytag_notnone_val(fixture_tag_logic_meta, tag_values, expected):
    """Test _anytag_notnone_val returns first non-'None' tag value."""
    estimators = _named_components(*[{"foo": v} for v in tag_values])

    result = fixture_tag_logic_meta._anytag_notnone_val("foo", estimators)

    assert result == expected


def test_anytag_notnone_set_sets_first_notnone(fixture_tag_logic_meta):
    """Test _anytag_notnone_set sets tag to first non-'None' component value."""
    estimators = _named_components({"foo": "None"}, {"foo": "x"}, {"foo": "y"})

    fixture_tag_logic_meta._anytag_notnone_set("foo", estimators)

    assert fixture_tag_logic_meta.get_tag("foo") == "x"


def test_anytag_notnone_set_all_none_leaves_tag(fixture_tag_logic_meta):
    """Test _anytag_notnone_set does not change tag if all component values 'None'."""
    fixture_tag_logic_meta.set_tags(foo="original")
    estimators = _named_components({"foo": "None"}, {"foo": "None"})

    fixture_tag_logic_meta._anytag_notnone_set("foo", estimators)

    assert fixture_tag_logic_meta.get_tag("foo") == "original"


@pytest.mark.parametrize(
    "tag_pairs, expected",
    [
        # (left, mid) per component
        # all left True before first mid -> linked and complete
        ([(True, False), (True, True), (False, False)], (True, True)),
        # mid in first position -> linked and complete, regardless of left
        ([(False, True), (False, False)], (True, True)),
        # left False before first mid -> not linked, not complete
        ([(True, False), (False, False), (True, True)], (False, False)),
        # left False in first position, no mid
        ([(False, False)], (False, False)),
        # all left True, no mid -> linked but not complete
        ([(True, False), (True, False)], (True, False)),
        # empty list -> linked but not complete
        ([], (True, False)),
    ],
)
def test_tagchain_is_linked(fixture_tag_logic_meta, tag_pairs, expected):
    """Test _tagchain_is_linked returns correct (linked, complete) tuple."""
    estimators = _named_components(
        *[{"left": left, "mid": mid} for left, mid in tag_pairs]
    )

    result = fixture_tag_logic_meta._tagchain_is_linked(
        left_tag_name="left", mid_tag_name="mid", estimators=estimators
    )

    assert result == expected


def test_tagchain_is_linked_custom_values(fixture_tag_logic_meta):
    """Test _tagchain_is_linked with non-default left_tag_val and mid_tag_val."""
    estimators = _named_components(
        {"left": "ok", "mid": "no"},
        {"left": "ok", "mid": "stop"},
        {"left": "bad", "mid": "no"},
    )
    kwargs = {"left_tag_name": "left", "mid_tag_name": "mid", "estimators": estimators}

    linked = fixture_tag_logic_meta._tagchain_is_linked(
        left_tag_val="ok", mid_tag_val="stop", **kwargs
    )
    assert linked == (True, True)

    # with default values True/True, the first component already breaks the chain
    not_linked = fixture_tag_logic_meta._tagchain_is_linked(**kwargs)
    assert not_linked == (False, False)


@pytest.mark.parametrize(
    "tag_pairs, expected_left, expected_mid",
    [
        # linked and complete -> both set to "linked" values
        ([(True, False), (True, True)], "L", "M"),
        # linked, not complete -> left set to linked value, mid to "not" value
        ([(True, False), (True, False)], "L", "M_not"),
        # not linked -> both set to "not" values
        ([(False, False), (True, True)], "L_not", "M_not"),
    ],
)
def test_tagchain_is_linked_set(
    fixture_tag_logic_meta, tag_pairs, expected_left, expected_mid
):
    """Test _tagchain_is_linked_set sets left and mid tags on self correctly."""
    # map bool components to the string values used in the call below
    to_left = {True: "L", False: "x"}
    to_mid = {True: "M", False: "y"}
    estimators = _named_components(
        *[{"left": to_left[left], "mid": to_mid[mid]} for left, mid in tag_pairs]
    )

    fixture_tag_logic_meta._tagchain_is_linked_set(
        left_tag_name="left",
        mid_tag_name="mid",
        estimators=estimators,
        left_tag_val="L",
        mid_tag_val="M",
        left_tag_val_not="L_not",
        mid_tag_val_not="M_not",
    )

    assert fixture_tag_logic_meta.get_tag("left") == expected_left
    assert fixture_tag_logic_meta.get_tag("mid") == expected_mid
