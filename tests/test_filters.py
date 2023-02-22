import pytest

from pypipeline.filter import INT_MAX, INT_MIN, FloatFilter, GlobFilter, IntFilter, RegexFilter


def test_int_filter():
    f = IntFilter.parse("100:500")
    assert f.low == 100
    assert f.high == 500
    assert IntFilter.parse(":500").low == INT_MIN
    assert IntFilter.parse(":").low == INT_MIN
    assert IntFilter.parse("").low == INT_MIN
    assert IntFilter.parse(None).low == INT_MIN
    assert IntFilter.parse("500:").high == INT_MAX
    with pytest.raises(ValueError):
        IntFilter.parse("2:1")
    with pytest.raises(ValueError):
        IntFilter.parse("1:2:3")


def test_float_filter():
    f = FloatFilter.parse("5.5:10.5")
    assert f.low == 5.5
    assert f.high == 10.5
    assert FloatFilter.parse(":10.5").low == INT_MIN
    assert FloatFilter.parse(":").low == INT_MIN
    assert FloatFilter.parse("").low == INT_MIN
    assert FloatFilter.parse(None).low == INT_MIN
    assert FloatFilter.parse("10.5:").high == INT_MAX
    with pytest.raises(ValueError):
        FloatFilter.parse("2.5:1.5")
    with pytest.raises(ValueError):
        FloatFilter.parse("1.5:2.5:3.5")
