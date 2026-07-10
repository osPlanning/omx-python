import uuid

import h5py
import numpy as np
import openmatrix as omx
import pytest
from openmatrix import validator


@pytest.fixture
def omx_file(tmp_path):
    """Provide a unique temporary OMX file path for each test."""
    return tmp_path / f"test{uuid.uuid4().hex}.omx"


@pytest.fixture
def valid_omx_file(omx_file):
    """Create a valid OMX file that passes all required checks."""
    with omx.open_file(omx_file, "w") as f:
        f.create_matrix("m1", obj=np.ones((5, 5), dtype=np.float64))
        f.create_mapping("zones", np.arange(1, 6))
    return omx_file


class TestPassOrFail:
    def test_pass(self):
        assert validator.pass_or_fail(True) == "Pass"

    def test_fail(self):
        assert validator.pass_or_fail(False) == "Fail"


class TestOpenFile:
    def test_open_file(self, valid_omx_file, capsys):
        mat_file = validator.open_file(valid_omx_file)
        captured = capsys.readouterr()
        assert "File contents:" in captured.out
        assert mat_file is not None
        mat_file.close()


class TestCheck1:
    """Check 1: Has OMX_VERSION attribute set to 0.2"""

    def test_valid_version(self, valid_omx_file, capsys):
        with omx.open_file(valid_omx_file, "r") as f:
            result = validator.check1(f)
            assert result[0]  # ok (use == for numpy bool compatibility)
            assert result[1]  # required
            assert result[2] == 1  # checknum

    def test_missing_version(self, tmp_path, capsys):
        omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
        with h5py.File(omx_file, "w") as f:
            f.create_group("data")
        with omx.open_file(omx_file, "r") as f:
            result = validator.check1(f)
            assert result[0] is False

    def test_wrong_version(self, tmp_path, capsys):
        omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
        with h5py.File(omx_file, "w") as f:
            f.attrs["OMX_VERSION"] = b"0.1"
        with omx.open_file(omx_file, "r") as f:
            result = validator.check1(f)
            assert result[0] is False


class TestCheck2:
    """Check 2: Has SHAPE array attribute set to two item integer array"""

    def test_valid_shape(self, valid_omx_file, capsys):
        with omx.open_file(valid_omx_file, "r") as f:
            result = validator.check2(f)
            assert result[0]  # use == for numpy bool compatibility
            assert result[2] == 2

    def test_missing_shape(self, tmp_path, capsys):
        omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
        with h5py.File(omx_file, "w") as f:
            f.attrs["OMX_VERSION"] = b"0.2"
        with omx.open_file(omx_file, "r") as f:
            result = validator.check2(f)
            assert result[0] is False


class TestCheck3:
    """Check 3: Has data group for matrices"""

    def test_valid_data_group(self, valid_omx_file, capsys):
        with omx.open_file(valid_omx_file, "r") as f:
            result = validator.check3(f)
            assert result[0] is True
            assert result[2] == 3

    def test_missing_data_group(self, tmp_path, capsys):
        omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
        with h5py.File(omx_file, "w") as f:
            f.attrs["OMX_VERSION"] = b"0.2"
        with omx.open_file(omx_file, "r") as f:
            result = validator.check3(f)
            assert result[0] is False


class TestCheck4:
    """Check 4: Matrix shape matches file shape"""

    def test_matching_shapes(self, valid_omx_file, capsys):
        with omx.open_file(valid_omx_file, "r") as f:
            result = validator.check4(f)
            assert result[0] is True
            assert result[2] == 4

    def test_no_matrices(self, tmp_path, capsys):
        omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
        with omx.open_file(omx_file, "w"):
            pass  # Empty file with data group but no matrices
        with omx.open_file(omx_file, "r") as f:
            result = validator.check4(f)
            assert result[0] is True  # Vacuously true - no matrices to check


class TestCheck5:
    """Check 5: Uses common data types (float or int) for matrices"""

    def test_valid_float_dtype(self, valid_omx_file, capsys):
        with omx.open_file(valid_omx_file, "r") as f:
            result = validator.check5(f)
            assert result[0] is True
            assert result[2] == 5

    def test_valid_int_dtype(self, omx_file, capsys):
        with omx.open_file(omx_file, "w") as f:
            f.create_matrix("m1", obj=np.ones((5, 5), dtype=np.int32))
        with omx.open_file(omx_file, "r") as f:
            result = validator.check5(f)
            assert result[0] is True


class TestCheck6:
    """Check 6: Matrices chunked for faster I/O"""

    def test_chunked_matrix(self, valid_omx_file, capsys):
        with omx.open_file(valid_omx_file, "r") as f:
            result = validator.check6(f)
            assert result[0] is True
            assert result[2] == 6

    def test_unchunked_matrix(self, tmp_path, capsys):
        omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
        with h5py.File(omx_file, "w") as f:
            f.attrs["OMX_VERSION"] = b"0.2"
            f.attrs["SHAPE"] = np.array([5, 5], dtype=np.int32)
            data = f.create_group("data")
            data.create_dataset("m1", data=np.ones((5, 5)), chunks=None)
        with omx.open_file(omx_file, "r") as f:
            result = validator.check6(f)
            assert result[0] is False


class TestCheck7:
    """Check 7: Uses zlib/gzip compression if compression used"""

    def test_gzip_compression(self, valid_omx_file, capsys):
        with omx.open_file(valid_omx_file, "r") as f:
            result = validator.check7(f)
            assert result[0] is True
            assert result[2] == 7

    def test_no_compression(self, tmp_path, capsys):
        omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
        with h5py.File(omx_file, "w") as f:
            f.attrs["OMX_VERSION"] = b"0.2"
            f.attrs["SHAPE"] = np.array([5, 5], dtype=np.int32)
            data = f.create_group("data")
            data.create_dataset("m1", data=np.ones((5, 5)))
        with omx.open_file(omx_file, "r") as f:
            result = validator.check7(f)
            # No compression is ok (just prints "None")
            assert result[0] is True

    def test_non_gzip_compression(self, tmp_path, capsys):
        omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
        with h5py.File(omx_file, "w") as f:
            f.attrs["OMX_VERSION"] = b"0.2"
            f.attrs["SHAPE"] = np.array([5, 5], dtype=np.int32)
            data = f.create_group("data")
            data.create_dataset("m1", data=np.ones((5, 5)), compression="lzf")
        with omx.open_file(omx_file, "r") as f:
            result = validator.check7(f)
            assert result[0] is False


class TestCheck8:
    """Check 8: Has NA attribute if desired (but not required)"""

    def test_no_na_attribute(self, valid_omx_file, capsys):
        with omx.open_file(valid_omx_file, "r") as f:
            result = validator.check8(f)
            assert result[0] is False  # NA not set
            assert result[1] is False  # Not required
            assert result[2] == 8

    def test_with_na_attribute(self, omx_file, capsys):
        with omx.open_file(omx_file, "w") as f:
            f.create_matrix("m1", obj=np.ones((5, 5)), attrs={"NA": -999})
        with omx.open_file(omx_file, "r") as f:
            result = validator.check8(f)
            assert result[0] is True


class TestCheck9:
    """Check 9: Has lookup group for labels/indexes if desired"""

    def test_has_lookup_group(self, valid_omx_file, capsys):
        with omx.open_file(valid_omx_file, "r") as f:
            result = validator.check9(f)
            assert result[0] is True
            assert result[1] is False  # Not required
            assert result[2] == 9

    def test_missing_lookup_group(self, tmp_path, capsys):
        omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
        with h5py.File(omx_file, "w") as f:
            f.attrs["OMX_VERSION"] = b"0.2"
            f.create_group("data")
        with omx.open_file(omx_file, "r") as f:
            result = validator.check9(f)
            assert result[0] is False


class TestCheck10:
    """Check 10: Lookup shapes are 1-d and match file shape"""

    def test_valid_lookup_shape(self, valid_omx_file, capsys):
        with omx.open_file(valid_omx_file, "r") as f:
            result = validator.check10(f)
            assert result[0] is True
            assert result[2] == 10

    def test_no_lookup_group(self, tmp_path, capsys):
        omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
        with h5py.File(omx_file, "w") as f:
            f.attrs["OMX_VERSION"] = b"0.2"
            f.create_group("data")
        with omx.open_file(omx_file, "r") as f:
            result = validator.check10(f)
            assert result[0] is False

    def test_invalid_lookup_shape(self, tmp_path, capsys):
        omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
        with h5py.File(omx_file, "w") as f:
            f.attrs["OMX_VERSION"] = b"0.2"
            f.attrs["SHAPE"] = np.array([5, 5], dtype=np.int32)
            f.create_group("data")
            lookup = f.create_group("lookup")
            lookup.create_dataset("zones", data=np.arange(10))  # Wrong size
        with omx.open_file(omx_file, "r") as f:
            result = validator.check10(f)
            assert result[0] is False


class TestCheck11:
    """Check 11: Uses common data types (int or str) for lookups"""

    def test_valid_int_lookup(self, valid_omx_file, capsys):
        with omx.open_file(valid_omx_file, "r") as f:
            result = validator.check11(f)
            assert result[0] is True
            assert result[2] == 11

    def test_no_lookup_group(self, tmp_path, capsys):
        omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
        with h5py.File(omx_file, "w") as f:
            f.attrs["OMX_VERSION"] = b"0.2"
            f.create_group("data")
        with omx.open_file(omx_file, "r") as f:
            result = validator.check11(f)
            assert result[0] is False

    def test_string_lookup(self, omx_file, capsys):
        with omx.open_file(omx_file, "w") as f:
            f.create_matrix("m1", obj=np.ones((3, 3)))
            # Use bytes for h5py compatibility (Unicode strings not directly supported)
            f.create_mapping("zones", np.array([b"A", b"B", b"C"]))
        with omx.open_file(omx_file, "r") as f:
            result = validator.check11(f)
            assert result[0]


class TestCheck12:
    """Check 12: Has Lookup DIM attribute (not supported)"""

    @pytest.mark.skip("Not supported by omx-python at this time")  # pragma: no cover
    def test_dim_not_supported(self, valid_omx_file, capsys):
        with omx.open_file(valid_omx_file, "r") as f:
            result = validator.check12(f)
            assert result[0] is False  # Not supported
            assert result[1] is False  # Not required
            assert result[2] == 12
            captured = capsys.readouterr()
            assert "Not supported" in captured.out


class TestRunChecks:
    def test_run_checks_valid_file(self, valid_omx_file, capsys):
        validator.run_checks(valid_omx_file)
        captured = capsys.readouterr()
        assert "Overall" in captured.out

    def test_run_checks_file_not_found(self, tmp_path):
        nonexistent = tmp_path / "nonexistent.omx"
        with pytest.raises(FileNotFoundError):
            validator.run_checks(nonexistent)

    def test_run_checks_invalid_hdf5(self, tmp_path, capsys):
        invalid_file = tmp_path / "invalid.omx"
        invalid_file.write_text("not an hdf5 file")
        validator.run_checks(invalid_file)
        captured = capsys.readouterr()
        assert "Unable to open" in captured.out

    def test_run_checks_with_error_result(self, tmp_path, capsys, monkeypatch):
        """Test run_checks prints ERROR when a check returns 4-tuple."""
        omx_file = tmp_path / f"test{uuid.uuid4().hex}.omx"
        with omx.open_file(omx_file, "w") as f:
            f.create_matrix("m1", obj=np.ones((5, 5)))

        # Monkeypatch check1 to return an error tuple
        original_check1 = validator.check1  # noqa: F841

        def mock_check1(mat_file, required=True, checknum=1):
            return (False, True, 1, "Simulated check error")

        monkeypatch.setattr(validator, "check1", mock_check1)
        validator.run_checks(omx_file)
        captured = capsys.readouterr()
        assert "ERROR" in captured.out
        assert "Simulated check error" in captured.out


class TestCommandLine:
    def test_command_line(self, valid_omx_file, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["validator", str(valid_omx_file)])
        validator.command_line()
        captured = capsys.readouterr()
        assert "Overall" in captured.out


class TestExceptionHandling:
    """Test exception handling in validator checks."""

    def test_check1_exception(self, capsys):
        """Test check1 handles exceptions gracefully."""

        class BadFile:
            @property
            def attrs(self):
                raise RuntimeError("Simulated error")

        result = validator.check1(BadFile())
        assert len(result) == 4  # (ok, required, checknum, error_msg)
        assert result[0] is False
        assert "Simulated error" in result[3]

    def test_check2_exception(self, capsys):
        """Test check2 handles exceptions gracefully."""

        class BadFile:
            @property
            def attrs(self):
                raise RuntimeError("Simulated error")

        result = validator.check2(BadFile())
        assert len(result) == 4
        assert result[0] is False

    def test_check3_exception(self, capsys):
        """Test check3 handles exceptions gracefully."""

        class BadFile:
            pass

        result = validator.check3(BadFile())
        assert len(result) == 4
        assert result[0] is False

    def test_check4_exception(self, capsys):
        """Test check4 handles exceptions gracefully."""

        class BadFile:
            @property
            def attrs(self):
                raise RuntimeError("Simulated error")

        result = validator.check4(BadFile())
        assert len(result) == 4
        assert result[0] is False

    def test_check5_exception(self, capsys):
        """Test check5 handles exceptions gracefully."""

        class BadFile:
            def list_matrices(self):
                raise RuntimeError("Simulated error")

        result = validator.check5(BadFile())
        assert len(result) == 4
        assert result[0] is False

    def test_check6_exception(self, capsys):
        """Test check6 handles exceptions gracefully."""

        class BadFile:
            def list_matrices(self):
                raise RuntimeError("Simulated error")

        result = validator.check6(BadFile())
        assert len(result) == 4
        assert result[0] is False

    def test_check7_exception(self, capsys):
        """Test check7 handles exceptions gracefully."""

        class BadFile:
            def list_matrices(self):
                raise RuntimeError("Simulated error")

        result = validator.check7(BadFile())
        assert len(result) == 4
        assert result[0] is False

    def test_check8_exception(self, capsys):
        """Test check8 handles exceptions gracefully."""

        class BadFile:
            def list_matrices(self):
                raise RuntimeError("Simulated error")

        result = validator.check8(BadFile())
        assert len(result) == 4
        assert result[0] is False

    def test_check9_exception(self, capsys):
        """Test check9 handles exceptions gracefully."""

        class BadFile:
            pass

        result = validator.check9(BadFile())
        assert len(result) == 4
        assert result[0] is False

    def test_check10_exception(self, capsys):
        """Test check10 handles exceptions gracefully."""

        class BadFile:
            pass

        result = validator.check10(BadFile())
        assert len(result) == 4
        assert result[0] is False

    def test_check11_exception(self, capsys):
        """Test check11 handles exceptions gracefully."""

        class BadFile:
            pass

        result = validator.check11(BadFile())
        assert len(result) == 4
        assert result[0] is False

    def test_check12_exception(self, capsys):
        """Test check12 handles exceptions gracefully."""

        class BadFile:
            pass

        result = validator.check12(BadFile())
        assert len(result) == 4
        assert result[0] is False
