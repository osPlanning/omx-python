# OMX Python API Documentation

The Python OMX API borrows heavily from PyTables. An OMX file extends the equivalent PyTables File object, so anything you can do in PyTables you can do with OMX as well. This API attempts to be very Pythonic, including dictionary-style lookup of matrix names.

* [Pre-requisites](#pre-requisites)
* [Installation](#installation)
* [Quick Start Code](#quick-start-sample-code)
* [Usage Notes](#usage-notes)
* [API Reference](#api-reference)

# Pre-requisites

Python 2.6+, PyTables 3.1+, and NumPy. Python 3 is now supported too. 

On Windows, the easiest way to get these is from [Anaconda](https://www.continuum.io/downloads#windows) or from Chris Gohlke's python binaries [page](http://www.lfd.uci.edu/~gohlke/pythonlibs/).  On Linux, your distribution already has these available. 

# Installation

The easiest way to get OMX on Python is to use pip. Get the latest package (called OpenMatrix) from the [Python Package Index](https://pypi.python.org/pypi)

  `pip install openmatrix`

This command will fetch openmatrix from the PyPi repository and download/install it for you. The package name "omx" was already taken on pip for a lame xml library that no one uses. Thus our little project goes by "openmatrix" on pip instead of "omx". This means your import statements should look like, 

  `import openmatrix as omx`

and NOT:

  `import omx`

# Quick-Start Sample Code

```python
from __future__ import print_function
import openmatrix as omx
import numpy as np

# Create some data
ones = np.ones((100,100))
twos = 2.0*ones

# Create an OMX file (will overwrite existing file!)
print('Creating myfile.omx')
myfile = omx.open_file('myfile.omx','w')   # use 'a' to append/edit an existing file

# Write to the file.
myfile['m1'] = ones
myfile['m2'] = twos
myfile['m3'] = ones + twos           # numpy array math is fast
myfile.close()

# Open an OMX file for reading only
print('Reading myfile.omx')
myfile = omx.open_file('myfile.omx')

print ('Shape:', myfile.shape())                 # (100,100)
print ('Number of tables:', len(myfile))         # 3
print ('Table names:', myfile.list_matrices())   # ['m1','m2',',m3']

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
myfile.close()                            # was opened read-only, so let's reopen.
myfile = omx.open_file('myfile.omx','a')  # append mode: read/write existing file

myfile['m1'].attrs.timeperiod = 'am'
myfile['m1'].attrs.mode = 'hwy'

myfile['m2'].attrs.timeperiod = 'md'

myfile['m3'].attrs.timeperiod = 'am'
myfile['m3'].attrs.mode = 'trn'

print('attributes:', myfile.list_all_attributes())       # ['mode','timeperiod']

# Use a DICT to select matrices via attributes:

all_am_trips = myfile[ {'timeperiod':'am'} ]                    # [m1,m3]
all_hwy_trips = myfile[ {'mode':'hwy'} ]                        # [m1]
all_am_trn_trips = myfile[ {'mode':'trn','timeperiod':'am'} ]   # [m3]

print('sum of some tables:', np.sum(all_am_trips))

# SUPER FANCY: Create a mapping to use TAZ numbers instead of matrix offsets
# --------------------------------------------------------------------------
# (any mapping would work, such as a mapping with large gaps between zone
#  numbers. For this simple case we'll just assume TAZ numbers are 1-100.)

taz_equivs = np.arange(1,101)                  # 1-100 inclusive

myfile.create_mapping('taz', taz_equivs)
print('mappings:', myfile.list_mappings()) # ['taz']

tazs = myfile.mapping('taz') # Returns a dict:  {1:0, 2:1, 3:2, ..., 100:99}
m3 = myfile['m3']
print('cell value:', m3[tazs[100]][tazs[100]]) # 3.0  (taz (100,100) is cell [99][99])

myfile.close()
```

# Testing
Testing is done with [nose](https://nose.readthedocs.io/en/latest/).  Run the tests via:

```
openmatrix\test> nosetests -v
```

# OMX File Validator
Included in this package is a command line OMX file validation tool used to validate OMX files against the specification.  The tool is added to the system PATH when the package is installed and can be run as follows:

```
omx-validate my_file.omx
```

# Usage Notes

### File Objects

OMX File objects extend Pytables.File, so all Pytables functions work normally. We've also added some useful stuff to make things even easier.

### Writing Data

Writing data to an OMX file is simple: You must provide a name, and you must provide either an existing numpy (or python) array, or a shape and an "atom". You can optionally provide a descriptive title, a list of tags, and other implementation minutiae.

The easiest way to do all that is to use python dictionary nomenclature: 

```python
myfile['matrixname'] = mynumpyobject
```

will call createMatrix() for you and populate it with the specified array. 

### Accessing Data

You can access matrix objects by name, using dictionary lookup e.g. `myfile['hwydist']` or using PyTables path notation, e.g. `myfile.root.hwydist`

### Matrix objects

OMX matrices extend numpy arrays. An OMX matrix object extends a Pytables/HDF5 "node" which means all HDF5 methods and properties behave normally. Generally these datasets are going to be numpy CArray objects of arbitrary shape.
You can access a matrix object by name using:

* dictionary syntax, e.g. `myfile['hwydist']`
* or by Pytables path syntax, e.g. `myfile.root.hwydist`

Once you have a matrix object, you can perform normal numpy math on it or you can access rows and columns pythonically:

```python
myfile['biketime'][0][0] = 0.60 * myfile['bikedist'][0][0]
total_trips = numpy.sum(myfile.root.trips)`
```

### Properties
Every Matrix has its own dictionary of key/value pair attributes (properties) which can be accessed using the standard Pytables .attrs field.  Add as many attributes as you like; attributes can be string, ints, floats, and lists:

```python
print mymatrix.attrs
print mymatrix.attrs.myfield
print mymatrix.attrs['myfield']
```

### Tags

If you create tags for your objects, you can also look up matrices by those tags. You can assign tags to any matrix using the 'tags' property attribute.  Tags are a list of strings, e.g. ['skims','am','hwy'].  To retrieve the list of matrices that matches a given set of tags, pass in a tuple of tags when using dictionary-style lookups:

```python
list_all_hwy_skims = mybigfile[ ('skims','hwy') ]
```

This will always return a list (which can be empty). A matrix will only be included in the returned list if ALL tags specified match exactly. Tags are case-sensitive.

### Mappings

A mapping allows rows and columns to be accessed using an integer value other than a zero-based offset. For instance zone numbers often start at "1" not "0", and there can be significant gaps between zone numbers; they're rarely fully sequential. An OMX file can contain multiple mappings.

* Use the dictionary from mapping() to translate from an key value to a matrix lookup offset, e.g. `taznumber[1] -> matrix[0]`
* Use the list from mapentries() to translate the other way; i.e. from an offset to an index value, e.g. `matrix[0] -> 1` (where 1 is the TAZ number).


# API Reference

## Global Properties

### `__version__`
OMX module version string.  Currently '0.3.5' as of this writing. This is the Python API version.

### `__omx_version__`
OMX file format version. Currently '0.2'. This is the OMX file format specification that omx-python adheres to.

### `open_file`(filename, mode='r', title='', root_uep='/', filters=Filters(complevel=1, complib='zlib', shuffle=True, bitshuffle=False, fletcher32=False, least_significant_digit=None), shape=None, **kwargs)
        Open or create a new OMX file. New files will be created with default
        zlib compression enabled.
        
        Parameters
        ----------
        filename : string
            Name or path and name of file
        mode : string
            'r' for read-only; 
            'w' to write (erases existing file); 
            'a' to read/write an existing file (will create it if doesn't exist).
            Ignored in read-only mode.
        title : string
            Short description of this file, used when creating the file. Default is ''.
            Ignored in read-only mode.
        filters : tables.Filters
            HDF5 default filter options for compression, shuffling, etc. Default for
            OMX standard file format is: zlib compression level 1, and shuffle=True. 
            Only specify this if you want something other than the recommended standard 
            HDF5 zip compression.
            'None' will create enormous uncompressed files.
            Only 'zlib' compression is guaranteed to be available on all HDF5 implementations.
            See HDF5 docs for more detail.
        shape: numpy.array
            Shape of matrices in this file. Default is None. Specify a valid shape 
            (e.g. (1200,1200)) to enforce shape-checking for all added objects. 
            If shape is not specified, the first added matrix will not be shape-checked 
            and all subsequently added matrices must match the shape of the first matrix.
            All tables in an OMX file must have the same shape.
        
        Returns
        -------
        f : openmatrix.File
            The file object for reading and writing.

## File Objects

### `create_mapping`(self, title, entries, overwrite=False)
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
        mapping : tables.array
            Returns the created mapping.
        
        Raises:
            LookupError : if the mapping exists and overwrite=False
    
### `create_matrix`(self, name, atom=None, shape=None, title='', filters=None, chunkshape=None, byteorder=None, createparents=False, obj=None, attrs=None)
        Create an OMX Matrix (CArray) at the root level. User must pass in either
        an existing numpy matrix, or a shape and an atom type.
        
        Parameters
        ----------
        name : string
            The name of this matrix. Stored in HDF5 as the leaf name.
        title : string
            Short description of this matrix. Default is ''.
        obj : numpy.CArray
            Existing numpy array from which to create this OMX matrix. If obj is passed in,
            then shape and atom can be left blank. If obj is not passed in, then a shape and
            atom must be specified instead. Default is None.
        shape : numpy.array
            Optional shape of the matrix. Shape is an int32 numpy array of format (rows,columns).
            If shape is not specified, an existing numpy CArray must be passed in instead, 
            as the 'obj' parameter. Default is None.
        atom : atom_type
            Optional atom type of the data. Can be int32, float32, etc. Default is None.
            If None specified, then obj parameter must be passed in instead.
        filters : tables.Filters
            Set of HDF5 filters (compression, etc) used for creating the matrix. 
            Default is None. See HDF5 documentation for details. Note: while the default here
            is None, the default set of filters set at the OMX parent file level is 
            zlib compression level 1. Those settings usually trickle down to the table level.
        attrs : dict
            Dictionary of attribute names and values to be attached to this matrix.
            Default is None.
        
        Returns
        -------
        matrix : tables.carray
            HDF5 CArray matrix
    
### `delete_mapping`(self, title)
        Remove a mapping.
        
        Raises:
        -------
        LookupError : if the specified mapping does not exist.
        
### `list_all_attributes`(self)
        Return set of all attributes used for any Matrix in this File
        
        Returns
        -------
        all_attributes : set
            The combined set of all attribute names that exist on any matrix in this file.
    
### `list_mappings`(self)
        List all mappings in this file
        
        Returns:
        --------
        mappings : list
            List of the names of all mappings in the OMX file. Mappings 
            are stored internally in the 'lookup' subset of the HDF5 file
            structure. Returns empty list if there are no mappings.
    
### `list_matrices`(self)
        List the matrix names in this File
        
        Returns
        -------
        matrices : list
            List of all matrix names stored in this OMX file.
    
### `map_entries`(self, title)
        Return a list of entries for the specified mapping.
        Throws LookupError if the specified mapping does not exist.
    
### `mapping`(self, title)
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
    
### `shape`(self)
        Get the one and only shape of all matrices in this File
        
        Returns
        -------
        shape : tuple
            Tuple of (rows,columns) for this matrix and file.
    
### `version`(self)
        Return the OMX file format of this OMX file, embedded in the OMX_VERSION file attribute.
        Returns None if the OMX_VERSION attribute is not set.


## Exceptions
* LookupError
* ShapeError
