from __future__ import print_function

import numpy as np

from .file import File as File
from .exceptions import ShapeError as ShapeError

# GLOBAL VARIABLES -----------
__version__ = "0.3.3"
__omx_version__ = b"0.2"


# GLOBAL FUNCTIONS -----------
def open_file(filename, mode="r", title="", filters=None, shape=None, **kwargs):
    """
    Open or create a new OMX file. New files will be created with default
    zlib compression enabled if filters is None.

    Parameters
    ----------
    filename : string
        Name or path and name of file
    mode : string
        'r' for read-only;
        'w' to write (erases existing file);
        'a' to read/write an existing file (will create it if doesn't exist).
        'r+' is also supported (read/write, must exist).
        Ignored in read-only mode.
    title : string
        Short description of this file, used when creating the file. Default is ''.
        Ignored in read-only mode.
    filters : dict or object
        HDF5 default filter options.
        Default for OMX standard file format is: zlib compression level 1, and shuffle=True.
    shape: array-like
        Shape of matrices in this file. Default is None. Specify a valid shape
        (e.g. (1000,1200)) to enforce shape-checking for all added objects.
        If shape is not specified, the first added matrix will not be shape-checked
        and all subsequently added matrices must match the shape of the first matrix.
        All tables in an OMX file must have the same shape.

    Returns
    -------
    f : openmatrix.File
        The file object for reading and writing.
    """

    # Default filters if None and mode is writing
    if filters is None and mode != "r":
        filters = {"complib": "zlib", "complevel": 1, "shuffle": True}

    f = File(filename, mode, title=title, filters=filters, **kwargs)

    # add omx structure if file is writable
    if mode != "r":
        # version number
        if "OMX_VERSION" not in f.attrs:
            f.attrs["OMX_VERSION"] = __omx_version__
        if "OMX_CREATED_WITH" not in f.attrs:
            f.attrs["OMX_CREATED_WITH"] = "python omx " + __version__

        # shape
        if shape:
            storeshape = np.array([shape[0], shape[1]], dtype=np.int32)
            f.attrs["SHAPE"] = storeshape

        # /data and /lookup folders
        if "data" not in f:
            f.create_group("data")
        if "lookup" not in f:
            f.create_group("lookup")

    return f


if __name__ == "__main__":
    print("OMX!")
