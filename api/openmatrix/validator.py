import os
from . import open_file as _open_file

def pass_or_fail(ok): 
    return("Pass" if ok else "Fail")
         
def open_file(filename):
    mat_file = _open_file(filename, "r")
    print("File contents:", filename)
    print(mat_file)
    return(mat_file)

def check1(mat_file, required=True, checknum=1):
    try:
        print('\nCheck 1: Has OMX_VERSION attribute set to 0.2')
        ok = mat_file.root._v_attrs['OMX_VERSION'] == b'0.2'
        print("  File version is 0.2:", pass_or_fail(ok))
        return(ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))

def check2(mat_file, required=True, checknum=2):
    try:
        print('\nCheck 2: Has SHAPE array attribute set to two item integer array')
        ok = len(mat_file.root._v_attrs['SHAPE']) == 2
        print("  Length is 2:", pass_or_fail(ok))
        ok_2 = int(mat_file.root._v_attrs['SHAPE'][0]) == mat_file.root._v_attrs['SHAPE'][0]
        print("  First item is integer:", pass_or_fail(ok_2))
        ok_3 = int(mat_file.root._v_attrs['SHAPE'][1]) == mat_file.root._v_attrs['SHAPE'][1]
        print("  Second item is integer:", pass_or_fail(ok_3))
        print('  Shape:', mat_file.shape())
        return(ok * ok_2 * ok_3, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))

def check3(mat_file, required=True, checknum=3):
    try:
        print('\nCheck 3: Has data group for matrices')
        ok = 'data' in map(lambda x: x._v_name, mat_file.list_nodes("/"))
        print("  Group:", pass_or_fail(ok))
        print('  Number of Matrices:', len(mat_file))
        print('  Matrix names:', mat_file.list_matrices())
        return(ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))

def check4(mat_file, required=True, checknum=4):
    try:
        print("\nCheck 4: Matrix shape matches file shape")
        ok = True
        for matrix in mat_file.list_matrices():
            ok_2 = (mat_file[matrix].shape == mat_file.root._v_attrs['SHAPE']).all()
            print("  Matrix shape: ", matrix, ":", mat_file[matrix].shape, ":", pass_or_fail(ok_2))
            ok = ok * ok_2
        return(ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))

def check5(mat_file, required=True, checknum=5):
    try:
        print('\nCheck 5: Uses common data types (float or int) for matrices')
        ok = True
        for matrix in mat_file.list_matrices():
            ok_2 = (mat_file[matrix].dtype == float) or (mat_file[matrix].dtype == int)
            print("  Matrix: ", matrix, ":", mat_file[matrix].dtype, ":", pass_or_fail(ok_2))
            ok = ok * ok_2
        return(ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))

def check6(mat_file, required=True, checknum=6):
    try:
        print('\nCheck 6: Matrices chunked for faster I/O')
        ok = True
        for matrix in mat_file.list_matrices():
            ok_2 = True if mat_file[matrix].chunkshape is not None else False
            print("  Matrix chunkshape: ", matrix, ":", mat_file[matrix].chunkshape, ":", pass_or_fail(ok_2))
            ok = ok * ok_2
        return(ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))

def check7(mat_file, required=False, checknum=7):
    try:
        print('\nCheck 7: Uses zlib compression if compression used')
        ok = True
        for matrix in mat_file.list_matrices():
            ok_2 = True if mat_file[matrix].filters.complib is not None else False
            if ok_2:
                ok_3 = mat_file[matrix].filters.complib == 'zlib'
                ok_2 = ok_2 * ok_3
                print("  Matrix compression library and level: ", matrix, ":", mat_file[matrix].filters.complib, ":", mat_file[matrix].filters.complevel, ":", pass_or_fail(ok_2))
            ok = ok * ok_2
        return(ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))

def check8(mat_file, required=False, checknum=8):
    try:
        print("\nCheck 8: Has NA attribute if desired (but not required)")
        ok = True
        for matrix in mat_file.list_matrices():
           ok_2 = mat_file[matrix].attrs.__contains__("NA")
           print("  Matrix NA attribute: ", matrix, ":", pass_or_fail(ok_2))
           ok = ok * ok_2
        return(ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))

def check9(mat_file, required=False, checknum=9):
    try:
        print('\nCheck 9: Has lookup group for labels/indexes if desired (but not required)')
        ok = 'lookup' in map(lambda x: x._v_name, mat_file.list_nodes("/"))
        print("  Group:", pass_or_fail(ok))
        if ok:
            print('  Number of Lookups:', len(mat_file.list_mappings()))
            print('  Lookups names:', mat_file.list_mappings())
        return(ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))

def check10(mat_file, required=False, checknum=10):
    try:
        print("\nCheck 10: Lookup shapes are 1-d and match file shape")
        ok = False
        if 'lookup' in map(lambda x: x._v_name, mat_file.list_nodes("/")):
            ok = True
            for lookup in mat_file.list_mappings():
                this_shape = mat_file.get_node(mat_file.root.lookup, lookup).shape
                ok_2 = len(this_shape)==1 and this_shape[0] in mat_file.root._v_attrs['SHAPE']
                print("  Lookup: ", lookup, ":", this_shape, ":", pass_or_fail(ok_2))
                ok = ok * ok_2
        return(ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))

def check11(mat_file, required=False, checknum=11):
    try:
        print('\nCheck 11: Uses common data types (int or str) for lookups')
        is_int = lambda x: x == int
        ok = False
        if 'lookup' in map(lambda x: x._v_name, mat_file.list_nodes("/")):
            ok = True
            for lookup in mat_file.list_mappings():
                try:
                    ok_2 = all(map(lambda x: x == int(x), mat_file.mapping(lookup).keys())) 
                except ValueError:
                    ok_2 = None
                if not ok_2:    
                    ok_2 = all(map(lambda x: x == str(x), mat_file.mapping(lookup).keys()))
                if not ok_2:    
                    ok_2 = all(map(lambda x: x == bytes(x), mat_file.mapping(lookup).keys()))
                this_dtype = mat_file.get_node(mat_file.root.lookup, lookup).dtype
                print("  Lookup: ", lookup, ":",this_dtype,":", pass_or_fail(ok_2))
                ok = ok * ok_2
        return(ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))

def check12(mat_file, required=False, checknum=12):
    try:
        print("\nCheck 12: Has Lookup DIM attribute of 0 (row) or 1 (column) if desired (but not required)")
        print("  Not supported at this time by the Python openmatrix package")
        ok = False
        if 'lookup' in map(lambda x: x._v_name, mat_file.list_nodes("/")):
            ok = False
        return(ok, required, checknum)
    except Exception as err:
        return (False, required, checknum, str(err))


def run_checks(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError(filename)
    try:
        mat_file = open_file(filename)
    except:
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
                    print("  Check", result[2], ":", "Required" if result[1] else "Not required", ":", pass_or_fail(result[0]))
                if result[1]:
                  overall_ok = overall_ok * result[0]
            print("  Overall : ", pass_or_fail(overall_ok))
        finally:
            mat_file.close()
    
    
def command_line():        
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', nargs=1, type=str, action="store", help='Open Matrix file to validate')
    args = parser.parse_args()
    run_checks(args.filename[0])
