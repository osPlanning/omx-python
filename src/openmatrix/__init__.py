from os import PathLike
from typing import Union, Literal, Optional, Any

from .exceptions import ShapeError as ShapeError
from .file import File as File, __version__ as __version__, __omx_version__ as __omx_version__


# GLOBAL FUNCTIONS -----------
def open_file(
    filename: Union[str, PathLike],
    mode: Literal["r", "w", "a", "r+", "w-", "x"] = "r",
    title: str = "",
    filters: Optional[dict[str, Any]] = None,
    shape: Optional[tuple[int, int]] = None,
    **kwargs,
) -> File:
    """
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
    """

    # Default filters if None and mode is writing
    if filters is None and mode != "r":
        filters = {"complib": "gzip", "complevel": 1, "shuffle": True}

    return File(filename, mode, title=title, filters=filters, shape=shape, **kwargs)


if __name__ == "__main__":  # pragma: no cover
    print("OMX!")
