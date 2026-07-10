# OMX Python API Documentation

The Python OMX API is built on top of h5py. An OMX file extends the equivalent h5py File object, so anything you can do in h5py you can do with OMX as well. This API attempts to be very Pythonic, including dictionary-style lookup of matrix names.

* [Pre-requisites](#pre-requisites)
* [Installation](#installation)
* [Quick Start Code](#quick-start-sample-code)
* [Testing](#testing)
* [OMX File Validator](#omx-file-validator)
* [Usage Notes](#usage-notes)
* [API Reference](#api-reference)

# Pre-requisites

Python 3.9+, h5py 2.10+, and NumPy.

Binaries for all these dependencies are readily available from PyPI and can be installed via pip.

# Installation

The easiest way to get OMX on Python is to use pip. Get the latest package (called OpenMatrix) from the [Python Package Index](https://pypi.python.org/pypi)

  `pip install openmatrix`

Using uv is also possible and much faster:

  `pip install uv`
  `uv pip install openmatrix`


This command will fetch openmatrix from the PyPi repository and download/install it for you. The package name "omx" was already taken on pip for a lame xml library that no one uses. Thus our little project goes by "openmatrix" on pip instead of "omx". This means your import statements should look like,

  `import openmatrix as omx`

and NOT:

  `import omx`

# Quick-Start Sample Code

```python
import openmatrix as omx
import numpy as np

# Create some data
ones = np.ones((100, 100))
twos = 2.0 * ones

# Create an OMX file (will overwrite existing file!)
print('Creating myfile.omx')
myfile = omx.open_file('myfile.omx', 'w')  # use 'a' to append/edit an existing file

# Write to the file.
myfile['m1'] = ones
myfile['m2'] = twos
myfile['m3'] = ones + twos  # numpy array math is fast
myfile.close()

# Open an OMX file for reading only
print('Reading myfile.omx')
myfile = omx.open_file('myfile.omx')

print('Shape:', myfile.shape())  # (100,100)
print('Number of tables:', len(myfile))  # 3
print('Table names:', myfile.list_matrices())  # ['m1','m2',',m3']

# Work with data. Pass a string to select matrix by name:
# -------------------------------------------------------
m1 = myfile['m1']
m2 = myfile['m2']
m3 = myfile['m3']

# halves = m1 * 0.5  # CRASH!  Don't modify an OMX object directly.
#                    # Create a new numpy array, and then edit it.
halves = np.array(m1) * 0.5

first_row = m2[0]
first_row[:] = 0.5 * first_row[:]

my_very_special_zone_value = m2[10][25]

# FANCY: Use attributes to find matrices
# --------------------------------------
myfile.close()  # was opened read-only, so let's reopen.
myfile = omx.open_file('myfile.omx', 'a')  # append mode: read/write existing file

myfile['m1'].attrs.timeperiod = 'am'
myfile['m1'].attrs.mode = 'hwy'

myfile['m2'].attrs.timeperiod = 'md'

myfile['m3'].attrs.timeperiod = 'am'
myfile['m3'].attrs.mode = 'trn'

print('attributes:', myfile.list_all_attributes())  # ['mode','timeperiod']

# Use a DICT to select matrices via attributes:

all_am_trips = myfile[{'timeperiod': 'am'}]  # [m1,m3]
all_hwy_trips = myfile[{'mode': 'hwy'}]  # [m1]
all_am_trn_trips = myfile[{'mode': 'trn', 'timeperiod': 'am'}]  # [m3]

print('sum of some tables:', np.sum(all_am_trips))

# SUPER FANCY: Create a mapping to use TAZ numbers instead of matrix offsets
# --------------------------------------------------------------------------
# (any mapping would work, such as a mapping with large gaps between zone
#  numbers. For this simple case we'll just assume TAZ numbers are 1-100.)

taz_equivs = np.arange(1, 101)  # 1-100 inclusive

myfile.create_mapping('taz', taz_equivs)
print('mappings:', myfile.list_mappings())  # ['taz']

tazs = myfile.mapping('taz')  # Returns a dict:  {1:0, 2:1, 3:2, ..., 100:99}
m3 = myfile['m3']
print('cell value:', m3[tazs[100]][tazs[100]])  # 3.0  (taz (100,100) is cell [99][99])

myfile.close()
```

# Testing
Testing is done with [pytest](https://docs.pytest.org/).  Run the tests via:

```
pytest
```

# OMX File Validator
Included in this package is a command line OMX file validation tool used to validate OMX files against the specification.  The tool is added to the system PATH when the package is installed and can be run as follows:

```
omx-validate my_file.omx
```

# Usage Notes

### File Objects

OMX File objects extend h5py.File, so most h5py functions work normally, some methods operate in a modified manner to be more useful rather than general methods. We've also added some useful stuff to make things even easier.

### Writing Data

Writing data to an OMX file is simple: You must provide a name, and you must provide either an existing numpy (or python) array, or a shape and dtype. You can optionally provide a descriptive title, a list of tags, and other implementation minutiae.

The easiest way to do all that is to use python dictionary nomenclature:

```python
myfile['matrixname'] = mynumpyobject
```

will call `create_matrix()` for you and populate it with the specified array.

### Accessing Data

You can access matrix objects by name, using dictionary lookup e.g. `myfile['hwydist']`.

### Matrix objects

OMX matrices are h5py Dataset objects. An OMX matrix object extends an h5py Dataset which means most h5py methods and properties behave normally.
You can access a matrix object by name using:

* dictionary syntax, e.g. `myfile['hwydist']`

Once you have a matrix object, you can perform normal numpy math on it or you can access rows and columns pythonically:

```python
myfile['biketime'][0][0] = 0.60 * myfile['bikedist'][0][0]
total_trips = np.sum(myfile.root.trips)`
```

### Properties
Every Matrix has its own dictionary of key/value pair attributes (properties) which can be accessed using the standard h5py .attrs field.  Add as many attributes as you like; attributes can be string, ints, floats, and lists:

```python
print(mymatrix.attrs)
print(mymatrix.attrs['myfield'])
print(mymatrix.attrs.items())
```

Files can be queried for all matrices that match a set of attributes via indexing with a dictionary of attribute name and value.

```python
myfile[{"myfield": 123}]
```

### Mappings

A mapping allows rows and columns to be accessed using an integer value other than a zero-based offset. For instance zone numbers often start at "1" not "0", and there can be significant gaps between zone numbers; they're rarely fully sequential. An OMX file can contain multiple mappings.

* Use the dictionary from mapping() to translate from an key value to a matrix lookup offset, e.g. `taznumber[1] -> matrix[0]`
* Use the list from mapentries() to translate the other way; i.e. from an offset to an index value, e.g. `matrix[0] -> 1` (where 1 is the TAZ number).


# API Reference

## Global Properties

### `__version__`
OMX module version string.  Currently '0.4.0' as of this writing. This is the Python API version.

### `__omx_version__`
OMX file format version. Currently '0.2'. This is the OMX file format specification that omx-python adheres to.

### `open_file(filename: Union[str, PathLike], mode: Literal["r", "w", "a", "r+", "w-", "x"] = "r", title: str = "", filters: Optional[dict[str, Any]] = None, shape: Optional[tuple[int, int]] = None, **kwargs,) -> File`
        Open or create a new OMX file. New files will be created with default
        gzip compression enabled if filters is None.

        Parameters
        ----------
        filename : string or PathLike
            Name or path and name of file
        mode : string
            'r' for read-only;
            'w' to write (erases existing file);
            'a' to read/write an existing file (will create it if doesn't exist).
            'r+' is also supported (read/write, must exist).
            'w- or x' create file, fail if exists.
        title : string
            Short description of this file, used when creating the file. Default is ''.
            Ignored in read-only mode.
        filters : dict, optional
            HDF5 default filter options.
            Default for OMX standard file format is: gzip compression level 1, and shuffle=True.
        shape: array-like
            Shape of matrices in this file. Default is None. Specify a valid shape
            (e.g. (1000,1200)) to enforce shape-checking for all added objects.
            If shape is not specified, the first added matrix will not be shape-checked
            and all subsequently added matrices must match the shape of the first matrix.
            All datasets in an OMX file must have the same shape.

        Returns
        -------
        f : openmatrix.File
            The file object for reading and writing.

## File Objects
        OMX File class, which contains all the methods for adding, removing, manipulating matrices
        and mappings in an OMX file.

### `version(self) -> Optional[str]`
        """
        Return the OMX file format of this OMX file, embedded in the OMX_VERSION file attribute.
        Returns None if the OMX_VERSION attribute is not set.
        """

### `create_matrix(self, name: str, shape: Optional[tuple[int, int]] = None, title: str = "", filters: Optional[dict[str, Any]] = None, chunks: Union[bool, tuple[int, int]] = True, obj: Optional[npt.NDArray[Union[np.integer, np.floating]]] = None, dtype: Optional[np.dtype] = None, attrs: Optional[dict] = None,) -> h5py.Dataset`
        Create an OMX matrix (Dataset) at the root level. You must pass either
        an existing NumPy array, or both shape and dtype.

        Parameters
        ----------
        name : string
            The name of this matrix. Stored in HDF5 as the leaf name.
        shape : tuple[int, int], optional
            Shape of the matrix as (rows, columns). If not specified, `obj` must be provided.
        title : string
            Short description of this matrix. Default is ''.
        filters : dict, optional
            HDF5 filter options used when creating the matrix, such as `complib`,
            `complevel`, `shuffle`, and `fletcher32`.
        chunks: bool or tuple[int, int]
            Enable HDF5 array chunking. A value of True enables HDF5 to guess the best chunk size. Chunk size may impact
            I/O performance.
        obj : numpy.NDArray, optional
            Existing NumPy array to store. If `obj` is passed, `shape` and `dtype`
            are inferred from the array.
        dtype: numpy.dtype, optional
            Data type to use for storage. Required when `obj` is None.
        attrs : dict
            Dictionary of attribute names and values to be attached to this matrix.
            Default is None.

        Returns
        -------
        matrix : h5py.Dataset
            HDF5 dataset matrix

### `shape(self) -> Optional[tuple[int, int]]`
        Get the one and only shape of all matrices in this File

        Returns
        -------
        shape : tuple
            Tuple of (rows,columns) for this matrix and file or None if a shape is not present and could not be
            inferred.

### `list_matrices(self) -> list[str]`
        List the matrix names in this File

        Returns
        -------
        matrices : list
            List of all matrix names stored in this OMX file.

### `list_all_attributes(self) -> list[str]`
        Return set of all attributes used for any Matrix in this File

        Returns
        -------
        all_attributes : set
            The combined set of all attribute names that exist on any matrix in this file.

### `data(self) -> h5py.Group`
        Return the '/data' group.

### `lookup(self) -> h5py.Group`
        Return the '/lookup' group.

### `list_mappings(self) -> list[str]`
        List all mappings in this file

        Returns:
        --------
        mappings : list
            List of the names of all mappings in the OMX file. Mappings
            are stored internally in the 'lookup' subset of the HDF5 file
            structure. Returns empty list if there are no mappings.

### `delete_mapping(self, title) -> None`
        Remove a mapping.

        Raises:
        -------
        LookupError : if the specified mapping does not exist.

### `delete_matrix(self, name) -> None`
        Remove a matrix.

        Raises:
        -------
        LookupError : if the specified matrix does not exist.

### `mapping(self, title) -> dict[Any, int]`
        Return dict containing key:value pairs for specified mapping. Keys
        represent the map item and value represents the array offset.

        Parameters:
        -----------
        title : string
            Name of the mapping to be returned

        Returns:
        --------
        mapping : dict
            Dictionary where each key is the map item, and the value
            represents the array offset.

        Raises:
        -------
        LookupError : if the specified mapping does not exist.

### `map_entries(self, title) -> list[Any]`
        Return a list of entries for the specified mapping.

        Parameters:
        -----------
        title : string
            Name of the mapping to be returned

        Returns:
        --------
        mappings : list
            List of entries for the specified mapping.

        Raises:
        -------
        LookupError : if the specified mapping does not exist.

### `create_mapping(self, title, entries, overwrite=False)`
        Create an equivalency index, which maps a raw data dimension to
        another integer value. Once created, mappings can be referenced by
        offset or by key.

        Parameters:
        -----------
        title : string
            Name of this mapping
        entries : list
            List of n equivalencies for the mapping. n must match one data
            dimension of the matrix.
        overwrite : boolean
            True to allow overwriting an existing mapping, False will raise
            a LookupError if the mapping already exists. Default is False.

        Returns:
        --------
        mapping : h5py.Dataset
            Returns the created mapping.

        Raises:
            LookupError : if the mapping exists and overwrite=False

### `__getitem__(self, key)`
        Return a matrix by name, a list of matrices by attributes, or a HDF5 group for given absolute path.


### `__len__(self)`
        Return the length of the '/data' group.

### `__setitem__(self, key, dataset)`
        Create a matrix with a given name.

        If a h5py.Dataset is provide that dataset is copied directly.

### `items(self)`
        Return the key value pairs of the '/data' group.

### `keys(self)`
        Return the keys of the '/data' group.

### `values(self)`
        Return the values of the '/data' group.

### `__delitem__(self, key)`
        Delete a matrix by name, or a HDF5 group for given absolute path.

### `__iter__(self)`
        Iterate over the matrices in this container.

### `__contains__(self, item)`
        Test if a name is with the '/data' group.

## Exceptions
* LookupError
* ShapeError
