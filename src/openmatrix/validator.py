import os

from . import open_file as _open_file


def pass_or_fail(ok):
    return "Pass" if ok else "Fail"


def open_file(filename):
    mat_file = _open_file(filename, "r")
    print("File contents:", filename)
    print(mat_file)
    return mat_file


def check1(mat_file, required=True, checknum=1):
    """Check 1: Has OMX_VERSION attribute set to 0.2"""
    try:
        print("\nCheck 1: Has OMX_VERSION attribute set to 0.2")
        version = mat_file.attrs.get("OMX_VERSION")
        # h5py may return bytes or string depending on version
        ok = version in (b"0.2", "0.2")
        print("  File version is 0.2:", pass_or_fail(ok))
        return (ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))


def check2(mat_file, required=True, checknum=2):
    """Check 2: Has SHAPE array attribute set to two item integer array"""
    try:
        print("\nCheck 2: Has SHAPE array attribute set to two item integer array")
        shape_attr = mat_file.attrs.get("SHAPE")
        ok = shape_attr is not None and len(shape_attr) == 2
        print("  Length is 2:", pass_or_fail(ok))
        ok_2 = int(shape_attr[0]) == shape_attr[0] if ok else False
        print("  First item is integer:", pass_or_fail(ok_2))
        ok_3 = int(shape_attr[1]) == shape_attr[1] if ok else False
        print("  Second item is integer:", pass_or_fail(ok_3))
        print("  Shape:", mat_file.shape())
        return (ok and ok_2 and ok_3, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))


def check3(mat_file, required=True, checknum=3):
    """Check 3: Has data group for matrices"""
    try:
        print("\nCheck 3: Has data group for matrices")
        ok = "data" in mat_file["/"]
        print("  Group:", pass_or_fail(ok))
        print("  Number of Matrices:", len(mat_file))
        print("  Matrix names:", mat_file.list_matrices())
        return (ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))


def check4(mat_file, required=True, checknum=4):
    """Check 4: Matrix shape matches file shape"""
    try:
        print("\nCheck 4: Matrix shape matches file shape")
        ok = True
        shape_attr = mat_file.attrs.get("SHAPE")
        file_shape = tuple(shape_attr) if shape_attr is not None else None
        for matrix in mat_file.list_matrices():
            matrix_shape = mat_file[matrix].shape
            ok_2 = matrix_shape == file_shape
            print("  Matrix shape: ", matrix, ":", matrix_shape, ":", pass_or_fail(ok_2))
            ok = ok and ok_2
        return (ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))


def check5(mat_file, required=True, checknum=5):
    """Check 5: Uses common data types (float or int) for matrices"""
    try:
        print("\nCheck 5: Uses common data types (float or int) for matrices")
        ok = True
        for matrix in mat_file.list_matrices():
            dtype = mat_file[matrix].dtype
            ok_2 = dtype.kind in ("f", "i", "u")  # float, signed int, unsigned int
            print("  Matrix: ", matrix, ":", dtype, ":", pass_or_fail(ok_2))
            ok = ok and ok_2
        return (ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))


def check6(mat_file, required=True, checknum=6):
    """Check 6: Matrices chunked for faster I/O"""
    try:
        print("\nCheck 6: Matrices chunked for faster I/O")
        ok = True
        for matrix in mat_file.list_matrices():
            chunks = mat_file[matrix].chunks
            ok_2 = chunks is not None
            print("  Matrix chunks: ", matrix, ":", chunks, ":", pass_or_fail(ok_2))
            ok = ok and ok_2
        return (ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))


def check7(mat_file, required=False, checknum=7):
    """Check 7: Uses zlib/gzip compression if compression used"""
    try:
        print("\nCheck 7: Uses zlib/gzip compression if compression used")
        ok = True
        for matrix in mat_file.list_matrices():
            compression = mat_file[matrix].compression
            compression_opts = mat_file[matrix].compression_opts
            if compression is not None:
                # h5py uses 'gzip' for zlib compression
                ok_2 = compression == "gzip"
                print(
                    "  Matrix compression library and level: ",
                    matrix,
                    ":",
                    compression,
                    ":",
                    compression_opts,
                    ":",
                    pass_or_fail(ok_2),
                )
                ok = ok and ok_2
            else:
                print("  Matrix compression: ", matrix, ": None")
        return (ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))


def check8(mat_file, required=False, checknum=8):
    """Check 8: Has NA attribute if desired (but not required)"""
    try:
        print("\nCheck 8: Has NA attribute if desired (but not required)")
        ok = True
        for matrix in mat_file.list_matrices():
            ok_2 = "NA" in mat_file[matrix].attrs
            print("  Matrix NA attribute: ", matrix, ":", pass_or_fail(ok_2))
            ok = ok and ok_2
        return (ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))


def check9(mat_file, required=False, checknum=9):
    """Check 9: Has lookup group for labels/indexes if desired (but not required)"""
    try:
        print("\nCheck 9: Has lookup group for labels/indexes if desired (but not required)")
        ok = "lookup" in mat_file["/"]
        print("  Group:", pass_or_fail(ok))
        if ok:
            print("  Number of Lookups:", len(mat_file.list_mappings()))
            print("  Lookups names:", mat_file.list_mappings())
        return (ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))


def check10(mat_file, required=False, checknum=10):
    """Check 10: Lookup shapes are 1-d and match file shape"""
    try:
        print("\nCheck 10: Lookup shapes are 1-d and match file shape")
        ok = False
        if "lookup" in mat_file["/"]:
            ok = True
            shape_attr = mat_file.attrs.get("SHAPE")
            file_shape = tuple(shape_attr) if shape_attr is not None else ()
            lookup_group = mat_file.lookup
            for lookup_name in mat_file.list_mappings():
                this_shape = lookup_group[lookup_name].shape
                ok_2 = len(this_shape) == 1 and this_shape[0] in file_shape
                print("  Lookup: ", lookup_name, ":", this_shape, ":", pass_or_fail(ok_2))
                ok = ok and ok_2
        return (ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))


def check11(mat_file, required=False, checknum=11):
    """Check 11: Uses common data types (int or str) for lookups"""
    try:
        print("\nCheck 11: Uses common data types (int or str) for lookups")
        ok = False
        if "lookup" in mat_file["/"]:
            ok = True
            lookup_group = mat_file.lookup
            for lookup_name in mat_file.list_mappings():
                dtype = lookup_group[lookup_name].dtype
                # Check if integer or string type
                ok_2 = dtype.kind in ("i", "u", "S", "U", "O")
                print("  Lookup: ", lookup_name, ":", dtype, ":", pass_or_fail(ok_2))
                ok = ok and ok_2
        return (ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))


def check12(mat_file, required=False, checknum=12):
    """Check 12: Has Lookup DIM attribute of 0 (row) or 1 (column) if desired (but not required)"""
    try:
        print("\nCheck 12: Has Lookup DIM attribute of 0 (row) or 1 (column) if desired (but not required)")
        print("  Not supported at this time by the Python openmatrix package")
        ok = "lookup" in mat_file["/"]
        return (ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))


def run_checks(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError(filename)
    try:
        mat_file = open_file(filename)
    except Exception:
        print("Unable to open", filename, "using HDF5")
    else:
        try:
            results = []
            results.append(check1(mat_file))
            results.append(check2(mat_file))
            results.append(check3(mat_file))
            results.append(check4(mat_file))
            results.append(check5(mat_file))
            results.append(check6(mat_file))
            results.append(check7(mat_file))
            results.append(check8(mat_file))
            results.append(check9(mat_file))
            results.append(check10(mat_file))
            results.append(check11(mat_file))
            results.append(check12(mat_file))
            print("\nOverall result ")
            overall_ok = True
            for result in results:
                if len(result) == 4:
                    print("  ERROR", result[3])
                else:
                    print(
                        "  Check",
                        result[2],
                        ":",
                        "Required" if result[1] else "Not required",
                        ":",
                        pass_or_fail(result[0]),
                    )
                if result[1]:
                    overall_ok = overall_ok and result[0]
            print("  Overall : ", pass_or_fail(overall_ok))
        finally:
            mat_file.close()


def command_line():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("filename", nargs=1, type=str, action="store", help="Open Matrix file to validate")
    args = parser.parse_args()
    run_checks(args.filename[0])
