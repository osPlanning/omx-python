import os
import tempfile
import pytest
import numpy as np
import numpy.testing as npt
import h5py
import openmatrix as omx

TEST_FILE = None


def ones5x5():
    return np.ones((5, 5))


def add_m1_node(f):
    f.create_matrix("m1", obj=ones5x5())


@pytest.fixture(autouse=True)
def setup_teardown():
    global TEST_FILE
    if TEST_FILE is not None and os.path.isfile(TEST_FILE):
        try:
            os.remove(TEST_FILE)
        except Exception:
            pass

    fd, TEST_FILE = tempfile.mkstemp(suffix=".omx")
    os.close(fd)
    os.remove(TEST_FILE)  # Start fresh

    yield

    if TEST_FILE is not None and os.path.isfile(TEST_FILE):
        try:
            os.remove(TEST_FILE)
        except Exception:
            pass
    TEST_FILE = None


def test_create_file():
    with omx.open_file(TEST_FILE, "w"):
        pass
    assert os.path.isfile(TEST_FILE)


def test_open_readonly_hdf5_file():
    with h5py.File(TEST_FILE, "w"):
        pass

    assert os.path.isfile(TEST_FILE)

    with omx.open_file(TEST_FILE, "r"):
        pass


def test_set_get_del():
    with omx.open_file(TEST_FILE, "w") as f:
        add_m1_node(f)
        npt.assert_array_equal(f["m1"], ones5x5())
        assert f.shape() == (5, 5)
        del f["m1"]
        assert "m1" not in f


def test_add_numpy_matrix_using_brackets():
    with omx.open_file(TEST_FILE, "w") as f:
        f["m1"] = ones5x5()
        npt.assert_array_equal(f["m1"], ones5x5())
        assert f.shape() == (5, 5)

        # test check for shape matching
        with pytest.raises(omx.exceptions.ShapeError):
            f.create_matrix("m2", obj=np.ones((8, 8)))


def test_add_numpy_matrix_using_create_matrix():
    with omx.open_file(TEST_FILE, "w") as f:
        f.create_matrix("m1", obj=ones5x5())
        npt.assert_array_equal(f["m1"], ones5x5())
        assert f.shape() == (5, 5)


def test_add_matrix_to_readonly_file():
    with omx.open_file(TEST_FILE, "w") as f:
        f["m2"] = np.ones((5, 5))

    with omx.open_file(TEST_FILE, "r") as f:
        with pytest.raises(ValueError):
            f.create_matrix("m1", obj=np.ones((5, 5)))


def test_add_matrix_with_same_name():
    with omx.open_file(TEST_FILE, "w") as f:
        add_m1_node(f)
        # now add m1 again:
        with pytest.raises((ValueError, RuntimeError)):
            add_m1_node(f)


def test_get_length_of_file():
    with omx.open_file(TEST_FILE, "w") as f:
        f["m1"] = np.ones((5, 5))
        f["m2"] = np.ones((5, 5))
        f["m3"] = np.ones((5, 5))
        f["m4"] = np.ones((5, 5))
        f["m5"] = np.ones((5, 5))
        assert len(f) == 5
        assert len(f.list_matrices()) == 5


def test_len_list_iter():
    names = ["m{}".format(x) for x in range(5)]
    with omx.open_file(TEST_FILE, "w") as f:
        for m in names:
            f[m] = ones5x5()

        for mat in f:
            npt.assert_array_equal(mat, ones5x5())

        assert len(f) == len(names)
        assert f.list_matrices() == names


def test_contains():
    with omx.open_file(TEST_FILE, "w") as f:
        add_m1_node(f)
        assert "m1" in f
        # keep this here to be sure we're actually running
        # File.__contains__
        assert "m1" in f


def test_contains_groups_and_datasets():
    with omx.open_file(TEST_FILE, "w") as f:
        # groups auto-created in writable mode
        assert "data" in f
        assert "lookup" in f

        f.create_mapping("zones", entries=np.array([1, 2, 3]))
        f.create_matrix("m1", obj=np.ones((5, 5)))

        assert "m1" in f  # dataset inside data
        assert "zones" in f.lookup  # dataset inside lookup group
        assert "missing" not in f


def test_list_all_attrs():
    with omx.open_file(TEST_FILE, "w") as f:
        add_m1_node(f)
        f["m2"] = ones5x5()

        assert f.list_all_attributes() == []

        f["m1"].attrs["a1"] = "a1"
        f["m1"].attrs["a2"] = "a2"
        f["m2"].attrs["a2"] = "a2"
        f["m2"].attrs["a3"] = "a3"

        assert f.list_all_attributes() == ["a1", "a2", "a3"]


def test_matrices_by_attr():
    with omx.open_file(TEST_FILE, "w") as f:
        f["m1"] = ones5x5()
        f["m2"] = ones5x5()
        f["m3"] = ones5x5()

        for m in f:
            m.attrs["a1"] = "a1"
            m.attrs["a2"] = "a2"
        f["m3"].attrs["a2"] = "a22"
        f["m3"].attrs["a3"] = "a3"

        gmba = f._getMatricesByAttribute

        assert gmba("zz", "zz") == []

        r1 = gmba("a1", "a1")
        assert len(r1) == 3
        names = sorted([m.name.split("/")[-1] for m in r1])
        assert names == ["m1", "m2", "m3"]

        r2 = gmba("a2", "a2")
        assert len(r2) == 2
        names2 = sorted([m.name.split("/")[-1] for m in r2])
        assert names2 == ["m1", "m2"]

        r3 = gmba("a2", "a22")
        assert len(r3) == 1
        assert r3[0].name.split("/")[-1] == "m3"

        r4 = gmba("a3", "a3")
        assert len(r4) == 1
        assert r4[0].name.split("/")[-1] == "m3"


def test_set_with_carray():
    with omx.open_file(TEST_FILE, "w") as f:
        f["m1"] = ones5x5()
        f["m2"] = f["m1"]
        npt.assert_array_equal(f["m2"], f["m1"])


def test_mappings():
    with omx.open_file(TEST_FILE, "w") as f:
        taz_equivs = np.arange(1, 4)
        f.create_mapping("taz", taz_equivs)

        tazs = f.mapping("taz")
        assert tazs == {1: 0, 2: 1, 3: 2}
        with pytest.raises(LookupError):
            f.mapping("missing")

        entries = f.map_entries("taz")
        assert entries == [1, 2, 3]
        with pytest.raises(LookupError):
            f.map_entries("missing")


def test_open_existing_with_append_mode():
    # Create file and add a matrix
    with omx.open_file(TEST_FILE, "w") as f:
        data = np.arange(9, dtype=float).reshape(3, 3)
        f.create_matrix("my_matrix", obj=data)

    # Re-open in append mode and ensure dataset is accessible
    with omx.open_file(TEST_FILE, "a") as f:
        assert "my_matrix" in f
        npt.assert_array_equal(f["my_matrix"], data)
