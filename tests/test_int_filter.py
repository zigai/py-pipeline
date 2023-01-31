import pytest

from pypipeline.filter import INT_MAX, IntFilter


def test_int_filter():
    f = IntFilter.parse("100:500")
    assert f.low == 100
    assert f.high == 500
    assert IntFilter.parse(":500").low == 0
    assert IntFilter.parse(":").low == 0
    assert IntFilter.parse("").low == 0
    assert IntFilter.parse(None).low == 0
    assert IntFilter.parse("500:").high == INT_MAX
    with pytest.raises(ValueError):
        IntFilter.parse("2:1")
    with pytest.raises(ValueError):
        IntFilter.parse("1:2:3")
