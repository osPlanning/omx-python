import uuid
import pytest
import numpy as np
import numpy.testing as npt
import h5py
import openmatrix as omx


@pytest.fixture
def omx_file(tmp_path):
    """Provide a unique temporary OMX file path for each test."""
    return tmp_path / f"test{uuid.uuid4().hex}.omx"


def ones5x5():
    return np.ones((5, 5))


def add_m1_node(f):
    f.create_matrix("m1", obj=ones5x5())


def test_create_file(omx_file):
    with omx.open_file(omx_file, "w"):
        pass
    assert omx_file.exists()


def test_open_readonly_hdf5_file(omx_file):
    with h5py.File(omx_file, "w"):
        pass

    assert omx_file.exists()

    with omx.open_file(omx_file, "r"):
        pass


def test_set_get_del(omx_file):
    with omx.open_file(omx_file, "w") as f:
        add_m1_node(f)
        npt.assert_array_equal(f["m1"], ones5x5())
        assert f.shape() == (5, 5)
        del f["m1"]
        assert "m1" not in f


def test_add_numpy_matrix_using_brackets(omx_file):
    with omx.open_file(omx_file, "w") as f:
        f["m1"] = ones5x5()
        npt.assert_array_equal(f["m1"], ones5x5())
        assert f.shape() == (5, 5)

        # test check for shape matching
        with pytest.raises(omx.exceptions.ShapeError):
            f.create_matrix("m2", obj=np.ones((8, 8)))


def test_add_numpy_matrix_using_create_matrix(omx_file):
    with omx.open_file(omx_file, "w") as f:
        f.create_matrix("m1", obj=ones5x5())
        npt.assert_array_equal(f["m1"], ones5x5())
        assert f.shape() == (5, 5)


def test_add_matrix_to_readonly_file(omx_file):
    with omx.open_file(omx_file, "w") as f:
        f["m2"] = np.ones((5, 5))

    with omx.open_file(omx_file, "r") as f:
        with pytest.raises(ValueError):
            f.create_matrix("m1", obj=np.ones((5, 5)))


def test_add_matrix_with_same_name(omx_file):
    with omx.open_file(omx_file, "w") as f:
        add_m1_node(f)
        # now add m1 again:
        with pytest.raises((ValueError, RuntimeError)):
            add_m1_node(f)


def test_get_length_of_file(omx_file):
    with omx.open_file(omx_file, "w") as f:
        f["m1"] = np.ones((5, 5))
        f["m2"] = np.ones((5, 5))
        f["m3"] = np.ones((5, 5))
        f["m4"] = np.ones((5, 5))
        f["m5"] = np.ones((5, 5))
        assert len(f) == 5
        assert len(f.list_matrices()) == 5


def test_len_list_iter(omx_file):
    names = ["m{}".format(x) for x in range(5)]
    with omx.open_file(omx_file, "w") as f:
        for m in names:
            f[m] = ones5x5()

        for mat in f:
            npt.assert_array_equal(mat, ones5x5())

        assert len(f) == len(names)
        assert f.list_matrices() == names


def test_contains(omx_file):
    with omx.open_file(omx_file, "w") as f:
        add_m1_node(f)
        assert "m1" in f


def test_contains_groups_and_datasets(omx_file):
    with omx.open_file(omx_file, "w") as f:
        # groups auto-created in writable mode
        assert "data" in f["/"] and "data" not in f
        assert "lookup" in f["/"] and "lookup" not in f

        f.create_mapping("zones", entries=np.array([1, 2, 3]))
        f.create_matrix("m1", obj=np.ones((5, 5)))

        assert "m1" in f and "m1" in f.data  # dataset inside data
        assert "zones" in f.lookup  # dataset inside lookup group
        assert "missing" not in f


def test_list_all_attrs(omx_file):
    with omx.open_file(omx_file, "w") as f:
        add_m1_node(f)
        f["m2"] = ones5x5()

        assert f.list_all_attributes() == []

        f["m1"].attrs["a1"] = "a1"
        f["m1"].attrs["a2"] = "a2"
        f["m2"].attrs["a2"] = "a2"
        f["m2"].attrs["a3"] = "a3"

        assert f.list_all_attributes() == ["a1", "a2", "a3"]


def test_matrices_by_attr(omx_file):
    with omx.open_file(omx_file, "w") as f:
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


def test_set_with_dataset_reference(omx_file):
    with omx.open_file(omx_file, "w") as f:
        f["m1"] = ones5x5()
        f["m2"] = f["m1"]
        npt.assert_array_equal(f["m2"], f["m1"])


def test_mappings(omx_file):
    with omx.open_file(omx_file, "w") as f:
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


def test_open_existing_with_append_mode(omx_file):
    data = np.arange(9, dtype=float).reshape(3, 3)
    # Create file and add a matrix
    with omx.open_file(omx_file, "w") as f:
        f.create_matrix("my_matrix", obj=data)

    # Re-open in append mode and ensure dataset is accessible
    with omx.open_file(omx_file, "a") as f:
        assert "my_matrix" in f
        npt.assert_array_equal(f["my_matrix"], data)


def test_lookup_property_behavior(tmp_path):
    omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
    # When writable, lookup is auto-created and returns an h5py Group
    with omx.open_file(omx_file, "w") as f:
        lookup_group = f.lookup
        assert isinstance(lookup_group, h5py.Group)
        assert "lookup" in f["/"] and "lookup" not in f
        lookup_group.create_dataset("zones", data=np.arange(3))

    # With an existing lookup group, read mode should expose it
    with omx.open_file(omx_file, "r") as f:
        assert "lookup" in f["/"] and "lookup" not in f
        assert "zones" in f.lookup

    # If a read-only file has no lookup group, accessing lookup should raise
    omx_file_no_lookup = tmp_path / f"test{uuid.uuid4().hex}.omx"
    with h5py.File(omx_file_no_lookup, "w"):
        pass
    with omx.open_file(omx_file_no_lookup, "r") as f:
        with pytest.raises(KeyError, match="object 'lookup' doesn't exist"):
            _ = f.lookup


def test_version_attribute(omx_file):
    """Test version() method returns OMX_VERSION or None."""
    # When file has OMX_VERSION (set by open_file in write mode)
    with omx.open_file(omx_file, "w") as f:
        ver = f.version()
        # version can be bytes or string depending on h5py version
        assert ver in (b"0.2", "0.2")

    # When file has no OMX_VERSION attribute
    omx_file_no_ver = omx_file.parent / f"test{uuid.uuid4().hex}.omx"
    with h5py.File(omx_file_no_ver, "w"):
        pass
    with omx.open_file(omx_file_no_ver, "r") as f:
        assert f.version() is None


def test_create_matrix_without_obj_raises(omx_file):
    """Test create_matrix raises ValueError when obj=None and shape/dtype not specified."""
    with omx.open_file(omx_file, "w") as f:
        with pytest.raises(ValueError, match="Shape and dtype must be specified"):
            f.create_matrix("test")


def test_create_matrix_with_shape_and_dtype(omx_file):
    """Test create_matrix with explicit shape and dtype (no obj)."""
    with omx.open_file(omx_file, "w") as f:
        mat = f.create_matrix("test", shape=(3, 3), dtype=np.float64)
        assert mat.shape == (3, 3)
        assert mat.dtype == np.float64


def test_create_matrix_with_title(omx_file):
    """Test create_matrix with title sets TITLE attribute."""
    with omx.open_file(omx_file, "w") as f:
        f.create_matrix("m1", obj=ones5x5(), title="My Matrix Title")
        assert f["m1"].attrs["TITLE"] == "My Matrix Title"


def test_create_matrix_with_attrs(omx_file):
    """Test create_matrix with custom attrs dict."""
    with omx.open_file(omx_file, "w") as f:
        f.create_matrix("m1", obj=ones5x5(), attrs={"custom1": "value1", "custom2": 42})
        assert f["m1"].attrs["custom1"] == "value1"
        assert f["m1"].attrs["custom2"] == 42


def test_create_matrix_with_dict_filters(omx_file):
    """Test create_matrix with dict-style filters including zlib->gzip conversion."""
    with omx.open_file(omx_file, "w") as f:
        filters = {"complib": "zlib", "complevel": 4, "shuffle": True}
        f.create_matrix("m1", obj=ones5x5(), filters=filters)
        assert f["m1"].compression == "gzip"
        assert f["m1"].compression_opts == 4
        assert f["m1"].shuffle is True


def test_create_matrix_with_invalid_filters_type_raises(omx_file):
    """Test create_matrix rejects non-dict filter values."""
    with omx.open_file(omx_file, "w") as f:
        with pytest.raises(TypeError, match="filters must be a dict or None"):
            f.create_matrix("m1", obj=ones5x5(), filters="gzip")


def test_open_file_with_invalid_filters_type_raises(omx_file):
    """Test open_file rejects non-dict default filters."""
    with pytest.raises(TypeError, match="filters must be a dict or None"):
        with omx.open_file(omx_file, "w", filters="gzip") as f:
            f["m1"] = ones5x5()


def test_shape_inferred_from_first_matrix(tmp_path):
    """Test shape() infers shape from first matrix when SHAPE attr is missing."""
    omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
    # Create file directly with h5py to skip OMX structure
    with h5py.File(omx_file, "w") as f:
        data_group = f.create_group("data")
        data_group.create_dataset("m1", data=np.ones((7, 7)))

    with omx.open_file(omx_file, "r") as f:
        shape = f.shape()
        assert shape == (7, 7)


def test_list_matrices_empty_file(tmp_path):
    """Test list_matrices returns empty list when no data group exists."""
    omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
    with omx.open_file(omx_file, "w"):
        pass
    with omx.open_file(omx_file, "r") as f:
        assert f.list_matrices() == []


def test_delete_mapping(omx_file):
    """Test delete_mapping removes a mapping."""
    with omx.open_file(omx_file, "w") as f:
        f.create_mapping("taz", np.arange(1, 6))
        assert "taz" in f.list_mappings()
        f.delete_mapping("taz")
        assert "taz" not in f.list_mappings()


@pytest.mark.parametrize(
    "setup,title",
    [
        ("no_lookup", "missing"),  # No lookup group exists
        ("with_mapping", "nonexistent"),  # Lookup exists but title doesn't
    ],
)
def test_delete_mapping_errors(tmp_path, setup, title):
    """Test delete_mapping raises LookupError for missing lookup or title."""
    omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
    if setup == "no_lookup":
        with h5py.File(omx_file, "w"):
            pass
        with omx.File(omx_file, "r+") as f:
            with pytest.raises(LookupError, match="No such mapping"):
                f.delete_mapping(title)
    else:
        with omx.open_file(omx_file, "w") as f:
            f.create_mapping("taz", np.arange(1, 6))
            with pytest.raises(LookupError, match="No such mapping"):
                f.delete_mapping(title)


@pytest.mark.parametrize("matrix_exists", [True, False])
def test_delete_matrix_behavior(omx_file, matrix_exists):
    """Test delete_matrix success and error cases."""
    with omx.open_file(omx_file, "w") as f:
        if matrix_exists:
            f.create_matrix("m1", obj=ones5x5())
            assert "m1" in f
            f.delete_matrix("m1")
            assert "m1" not in f
        else:
            with pytest.raises(LookupError, match="No such matrix"):
                f.delete_matrix("nonexistent")


@pytest.mark.parametrize("method", ["mapping", "map_entries"])
def test_mapping_methods_missing_lookup(tmp_path, method):
    """Test mapping() and map_entries() raise when lookup group doesn't exist."""
    omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
    with h5py.File(omx_file, "w"):
        pass
    with omx.open_file(omx_file, "r") as f:
        with pytest.raises(KeyError, match="object 'lookup' doesn't exist"):
            getattr(f, method)("missing")


def test_create_mapping_shape_mismatch(omx_file):
    """Test create_mapping raises ShapeError when entries don't match shape."""
    with omx.open_file(omx_file, "w") as f:
        f.create_matrix("m1", obj=ones5x5())  # Sets shape to (5,5)
        with pytest.raises(omx.exceptions.ShapeError, match="Mapping must match one data dimension"):
            f.create_mapping("bad", np.arange(1, 10))  # Length 9 doesn't match 5


@pytest.mark.parametrize(
    "overwrite,should_raise",
    [
        (True, False),  # overwrite=True replaces existing
        (False, True),  # overwrite=False raises
    ],
)
def test_create_mapping_overwrite_behavior(omx_file, overwrite, should_raise):
    """Test create_mapping overwrite parameter behavior."""
    with omx.open_file(omx_file, "w") as f:
        f.create_mapping("taz", np.arange(1, 4))
        if should_raise:
            with pytest.raises(LookupError, match="mapping already exists"):
                f.create_mapping("taz", np.arange(10, 13), overwrite=overwrite)
        else:
            f.create_mapping("taz", np.arange(10, 13), overwrite=overwrite)
            assert f.map_entries("taz") == [10, 11, 12]


def test_getitem_direct_group_access(omx_file):
    """Test __getitem__ with 'data' and 'lookup' keys."""
    with omx.open_file(omx_file, "w") as f:
        data_group = f.data
        assert isinstance(data_group, h5py.Group)
        lookup_group = f.lookup
        assert isinstance(lookup_group, h5py.Group)


def test_getitem_path_access(omx_file):
    """Test __getitem__ with absolute path."""
    with omx.open_file(omx_file, "w") as f:
        f.create_matrix("m1", obj=ones5x5())
        mat = f["/data/m1"]
        npt.assert_array_equal(mat, ones5x5())


def test_getitem_dict_attribute_lookup(omx_file):
    """Test __getitem__ with dict for attribute-based lookup."""
    with omx.open_file(omx_file, "w") as f:
        f["m1"] = ones5x5()
        f["m2"] = ones5x5()
        f["m1"].attrs["purpose"] = "work"
        f["m2"].attrs["purpose"] = "home"

        result = f[{"purpose": "work"}]
        assert len(result) == 1
        assert result[0].name.split("/")[-1] == "m1"


@pytest.mark.parametrize(
    "key,desc",
    [
        ("nonexistent", "missing string key"),
        (12345, "invalid key type without keys() method"),
    ],
)
def test_getitem_errors(omx_file, key, desc):
    """Test __getitem__ raises LookupError for invalid keys."""
    with omx.open_file(omx_file, "w") as f:
        with pytest.raises(LookupError, match="Key .* not found"):
            _ = f[key]


def test_getMatricesByAttribute_no_matrices_arg(omx_file):
    """Test _getMatricesByAttribute when matrices=None."""
    with omx.open_file(omx_file, "w") as f:
        f["m1"] = ones5x5()
        f["m1"].attrs["tag"] = "yes"
        result = f._getMatricesByAttribute("tag", "yes")  # matrices=None by default
        assert len(result) == 1


@pytest.mark.parametrize(
    "operation,expected",
    [
        ("len", 0),
        ("iter", []),
        ("contains", False),
    ],
)
def test_empty_file_no_data_group(tmp_path, operation, expected):
    """Test file operations when no data group exists."""
    omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
    with omx.open_file(omx_file, "w"):
        pass
    with omx.open_file(omx_file, "r") as f:
        if operation == "len":
            assert len(f) == expected
        elif operation == "iter":
            assert list(f) == expected
        elif operation == "contains":
            assert ("anything" in f) == expected
        else:  # pragma: no cover
            pass


def test_setitem_overwrites_existing(omx_file):
    """Test __setitem__ overwrites existing matrix."""
    with omx.open_file(omx_file, "w") as f:
        f["m1"] = ones5x5()
        f["m1"] = np.zeros((5, 5))
        npt.assert_array_equal(f["m1"], np.zeros((5, 5)))


@pytest.mark.parametrize("key_exists", [True, False])
def test_delitem_behavior(omx_file, key_exists):
    """Test __delitem__ for existing and non-existent keys."""
    with omx.open_file(omx_file, "w") as f:
        if key_exists:
            f["custom"] = ones5x5()
            assert "custom" in f
            del f["custom"]
            assert "custom" not in f
        else:
            with pytest.raises(KeyError, match="Couldn't delete link"):
                del f["nonexistent"]


def test_open_file_with_shape(omx_file):
    """Test open_file with shape parameter sets SHAPE attribute."""
    with omx.open_file(omx_file, "w", shape=(100, 200)) as f:
        shape = f.attrs["SHAPE"]
        assert tuple(shape) == (100, 200)


def test_create_matrix_with_non_zlib_compression(omx_file):
    """Test create_matrix with non-zlib compression (e.g., gzip directly)."""
    with omx.open_file(omx_file, "w") as f:
        filters = {"complib": "gzip", "complevel": 5, "shuffle": False}
        f.create_matrix("m1", obj=ones5x5(), filters=filters)
        assert f["m1"].compression == "gzip"
        assert f["m1"].compression_opts == 5


def test_shape_inferred_from_first_matrix_append_mode(tmp_path):
    """Test shape() infers and stores shape when mode is not read-only."""
    omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
    # Create file directly with h5py without SHAPE attribute
    with h5py.File(omx_file, "w") as f:
        data_group = f.create_group("data")
        data_group.create_dataset("m1", data=np.ones((7, 7)))

    # Open in append mode - shape should be inferred and stored
    with omx.open_file(omx_file, "a") as f:
        shape = f.shape()
        assert shape == (7, 7)
        # Verify SHAPE was stored in attrs
        assert "SHAPE" in f.attrs
        assert tuple(f.attrs["SHAPE"]) == (7, 7)


def test_getMatricesByAttribute_no_data_group(tmp_path):
    """Test _getMatricesByAttribute when no data group exists and matrices=None."""
    omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
    with omx.open_file(omx_file, "w"):
        pass

    with omx.open_file(omx_file, "r") as f:
        result = f._getMatricesByAttribute("key", "value")
        assert result == []


def test_setitem_with_h5py_dataset(omx_file):
    """Test __setitem__ when passing an h5py.Dataset (copy scenario)."""
    with omx.open_file(omx_file, "w") as f:
        f["m1"] = ones5x5()
        # Get the dataset and assign it to a new key
        dataset = f["m1"]
        f["m2"] = dataset
        # Both should have the same data
        npt.assert_array_equal(f["m1"], f["m2"])


def test_map_entries_non_numpy_array(tmp_path):
    """Test map_entries when entries don't have tolist method."""
    omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
    with omx.open_file(omx_file, "w") as f:
        # Create mapping normally
        f.create_mapping("taz", np.arange(1, 4))
        # Test that map_entries works
        entries = f.map_entries("taz")
        assert entries == [1, 2, 3]


def test_backward_compatibility_aliases(omx_file):
    """Test backward compatibility method aliases."""
    with omx.open_file(omx_file, "w") as f:
        # Test createMatrix alias
        f.createMatrix("m1", obj=ones5x5())
        assert "m1" in f

        # Test listMatrices alias
        assert f.listMatrices() == ["m1"]

        # Test listAllAttributes alias
        assert f.listAllAttributes() == []

        # Test createMapping alias
        f.createMapping("taz", np.arange(1, 6))
        assert "taz" in f.listMappings()

        # Test mapEntries alias
        assert f.mapEntries("taz") == [1, 2, 3, 4, 5]

        # Test deleteMapping alias
        f.deleteMapping("taz")
        assert "taz" not in f.listMappings()


def test_keys_values_items(omx_file):
    with omx.open_file(omx_file, "w") as f:
        f["m1"] = ones5x5()
        f["m2"] = ones5x5()

        assert all((k, v) == t for k, v, t in zip(f.keys(), f.values(), f.items()))


def test_assess_with_path(omx_file):
    with omx.open_file(omx_file, "w") as f:
        f["m1"] = ones5x5()
        npt.assert_array_equal(f["/data/m1"], ones5x5())

        del f["/data/m1"]

        assert "m1" not in f



@pytest.mark.parametrize("chunks", [True, False])
def test_chunks(omx_file, chunks):
    with omx.open_file(omx_file, "w") as f:
        f.create_matrix("m1", obj=ones5x5(), chunks=chunks)
