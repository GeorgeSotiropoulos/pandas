import pytest

import pandas.util._test_decorators as td

from pandas import DataFrame
import pandas._testing as tm


@td.skip_if_no("numba", "0.46.0")
def test_correct_function_signature():
    def incorrect_function(x):
        return x + 1

    data = DataFrame(
        {"key": ["a", "a", "b", "b", "a"], "data": [1.0, 2.0, 3.0, 4.0, 5.0]},
        columns=["key", "data"],
    )
    with pytest.raises(ValueError, match=f"The first 2"):
        data.groupby("key").transform(incorrect_function, engine="numba")

    with pytest.raises(ValueError, match=f"The first 2"):
        data.groupby("key")["data"].transform(incorrect_function, engine="numba")


@td.skip_if_no("numba", "0.46.0")
def test_check_nopython_kwargs():
    def incorrect_function(x, **kwargs):
        return x + 1

    data = DataFrame(
        {"key": ["a", "a", "b", "b", "a"], "data": [1.0, 2.0, 3.0, 4.0, 5.0]},
        columns=["key", "data"],
    )
    with pytest.raises(ValueError, match="numba does not support"):
        data.groupby("key").transform(incorrect_function, engine="numba", a=1)

    with pytest.raises(ValueError, match="numba does not support"):
        data.groupby("key")["data"].transform(incorrect_function, engine="numba", a=1)


@td.skip_if_no("numba", "0.46.0")
@pytest.mark.filterwarnings("ignore:\\nThe keyword argument")
# Filter warnings when parallel=True and the function can't be parallelized by Numba
@pytest.mark.parametrize("jit", [True, False])
@pytest.mark.parametrize("pandas_obj", ["Series", "DataFrame"])
def test_numba_vs_cython(jit, pandas_obj, nogil, parallel, nopython):
    def func(values, index):
        return values + 1

    if jit:
        # Test accepted jitted functions
        import numba

        func = numba.jit(func)

    data = DataFrame(
        {0: ["a", "a", "b", "b", "a"], 1: [1.0, 2.0, 3.0, 4.0, 5.0]}, columns=[0, 1],
    )
    engine_kwargs = {"nogil": nogil, "parallel": parallel, "nopython": nopython}
    grouped = data.groupby(0)
    if pandas_obj == "Series":
        grouped = grouped[1]

    result = grouped.transform(func, engine="numba", engine_kwargs=engine_kwargs)
    expected = grouped.transform(lambda x: x + 1, engine="cython")

    tm.assert_equal(result, expected)


@td.skip_if_no("numba", "0.46.0")
@pytest.mark.filterwarnings("ignore:\\nThe keyword argument")
# Filter warnings when parallel=True and the function can't be parallelized by Numba
@pytest.mark.parametrize("jit", [True, False])
@pytest.mark.parametrize("pandas_obj", ["Series", "DataFrame"])
def test_cache(jit, pandas_obj, nogil, parallel, nopython):
    # Test that the functions are cached correctly if we switch functions
    def func_1(values, index):
        return values + 1

    def func_2(values, index):
        return values * 5

    if jit:
        import numba

        func_1 = numba.jit(func_1)
        func_2 = numba.jit(func_2)

    data = DataFrame(
        {0: ["a", "a", "b", "b", "a"], 1: [1.0, 2.0, 3.0, 4.0, 5.0]}, columns=[0, 1],
    )
    engine_kwargs = {"nogil": nogil, "parallel": parallel, "nopython": nopython}
    grouped = data.groupby(0)
    if pandas_obj == "Series":
        grouped = grouped[1]

    result = grouped.transform(func_1, engine="numba", engine_kwargs=engine_kwargs)
    expected = grouped.transform(lambda x: x + 1, engine="cython")
    tm.assert_equal(result, expected)
    # func_1 should be in the cache now
    assert func_1 in grouped._numba_func_cache

    # Add func_2 to the cache
    result = grouped.transform(func_2, engine="numba", engine_kwargs=engine_kwargs)
    expected = grouped.transform(lambda x: x * 5, engine="cython")
    tm.assert_equal(result, expected)
    assert func_2 in grouped._numba_func_cache

    # Retest func_1 which should use the cache
    result = grouped.transform(func_1, engine="numba", engine_kwargs=engine_kwargs)
    expected = grouped.transform(lambda x: x + 1, engine="cython")
    tm.assert_equal(result, expected)
