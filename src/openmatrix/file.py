from os import PathLike
from typing import Optional, Union, Any, Literal

import h5py
import numpy as np
import numpy.typing as npt

from .exceptions import ShapeError


__version__ = "0.4.0"
__omx_version__ = b"0.2"


class File(h5py.File):
    """
    OMX File class, which contains all the methods for adding, removing, manipulating matrices
    and mappings in an OMX file.
    """

    def __init__(
        self,
        name: Union[str, PathLike],
        mode: Literal["r", "w", "a", "r+", "w-", "x"],
        title: str = "",
        filters: Optional[dict[str, Any]] = None,
        shape: Optional[tuple[int, int]] = None,
        **kwargs,
    ):
        super().__init__(name, mode, **kwargs)
        self._shape = None

        if filters is not None and not isinstance(filters, dict):
            raise TypeError("filters must be a dict or None")
        self.default_filters = filters

        # add omx structure if file is writable
        if mode != "r":
            # title
            if title:
                self.attrs["TITLE"] = title

            # version number
            if "OMX_VERSION" not in self.attrs:
                self.attrs["OMX_VERSION"] = __omx_version__
            if "OMX_CREATED_WITH" not in self.attrs:
                self.attrs["OMX_CREATED_WITH"] = "python omx " + __version__

            # shape
            if shape:
                storeshape = np.array([shape[0], shape[1]], dtype=np.int32)
                self.attrs["SHAPE"] = storeshape

            # /data and /lookup folders
            if "data" not in self["/"]:
                self.create_group("data")
            if "lookup" not in self["/"]:
                self.create_group("lookup")

    def version(self) -> Optional[str]:
        """
        Return the OMX file format of this OMX file, embedded in the OMX_VERSION file attribute.
        Returns None if the OMX_VERSION attribute is not set.
        """
        if "OMX_VERSION" in self.attrs:
            return self.attrs["OMX_VERSION"]
        else:
            return None

    def create_matrix(
        self,
        name: str,
        shape: Optional[tuple[int, int]] = None,
        title: str = "",
        filters: Optional[dict[str, Any]] = None,
        chunks: Union[bool, tuple[int, int]] = True,
        obj: Optional[npt.NDArray[Union[np.integer, np.floating]]] = None,
        dtype: Optional[np.dtype] = None,
        attrs: Optional[dict] = None,
    ) -> h5py.Dataset:
        """
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
            Enable HDF5 array chunking. A value of True lets HDF5 choose a chunk size.
            Chunk size may impact I/O performance.
        obj : numpy.NDArray, optional
            Existing NumPy array to store. If `obj` is passed, `shape` and `dtype`
            are inferred from the array.
        dtype: numpy.dtype, optional
            Data type to use for storage. Required when `obj` is None.
        attrs : dict
            Dictionary of attribute names and values to attach to this matrix.
            Default is None.

        Returns
        -------
        matrix : h5py.Dataset
            HDF5 dataset matrix
        """

        # If object was passed in, make sure its shape is correct
        if self.shape() is not None and obj is not None and obj.shape != self.shape():
            raise ShapeError(f"{name} has shape {obj.shape} but this file requires shape {self.shape()}")

        # Determine dshape and dtype
        dshape = shape
        data = obj
        if obj is not None:
            dshape = obj.shape
            dtype = obj.dtype

        if dshape is None or dtype is None:
            raise ValueError("Shape and dtype must be specified if obj is None")

        # Handle compression
        compression = compression_opts = None
        shuffle = fletcher32 = False

        # Use file defaults only when method-level filters are not provided.
        filters = self.default_filters if filters is None else filters

        if filters is not None:
            if not isinstance(filters, dict):
                raise TypeError("filters must be a dict or None")
            compression = filters.get("complib")
            compression_opts = filters.get("complevel")
            shuffle = filters.get("shuffle")
            fletcher32 = filters.get("fletcher32")

        compression = "gzip" if compression == "zlib" else compression

        # create_dataset arguments
        kwargs = {}
        if compression:
            kwargs["compression"] = compression
        if compression_opts is not None:
            kwargs["compression_opts"] = compression_opts
        if shuffle:
            kwargs["shuffle"] = shuffle
        if fletcher32:
            kwargs["fletcher32"] = fletcher32
        if chunks:
            kwargs["chunks"] = chunks

        matrix = super().__getitem__("data").create_dataset(name, shape=dshape, dtype=dtype, data=data, **kwargs)

        if title:
            matrix.attrs["TITLE"] = title

        # Store shape if we don't have one yet
        if self._shape is None:
            storeshape = np.array([matrix.shape[0], matrix.shape[1]], dtype="int32")
            self.attrs["SHAPE"] = storeshape
            self._shape = matrix.shape

        # attributes
        if attrs:
            for key in attrs:
                matrix.attrs[key] = attrs[key]

        return matrix

    def shape(self) -> Optional[tuple[int, int]]:
        """
        Get the one and only shape of all matrices in this File

        Returns
        -------
        shape : tuple
            Tuple of (rows,columns) for this matrix and file or None if a shape is not present and could not be
            inferred.
        """

        # If we already have the shape, just return it
        if self._shape:
            return self._shape

        # If shape is already set in root node attributes, grab it
        if "SHAPE" in self.attrs:
            # Shape is stored as a numpy.array:
            arrayshape = self.attrs["SHAPE"]
            # which must be converted to a tuple:
            self._shape = (arrayshape[0], arrayshape[1])
            return self._shape

        # Inspect the first Dataset object to determine its shape
        data_group = self.data
        if len(data_group) > 0:
            # Get first key
            first_key = list(data_group.keys())[0]
            self._shape = data_group[first_key].shape

            # Store it if we can
            if self.mode != "r":
                storeshape = np.array([self._shape[0], self._shape[1]], dtype="int32")
                self.attrs["SHAPE"] = storeshape
                self.flush()

            return self._shape
        return None

    def list_matrices(self) -> list[str]:
        """
        List the matrix names in this File

        Returns
        -------
        matrices : list
            List of all matrix names stored in this OMX file.
        """

        # Previous versions of OMX returned only matrix-like arrays. Current behavior
        # returns all children under '/data'.
        return list(self.data.keys())

    def list_all_attributes(self) -> list[str]:
        """
        Return set of all attributes used for any Matrix in this File

        Returns
        -------
        all_attributes : set
            The combined set of all attribute names that exist on any matrix in this file.
        """
        return sorted(set(k for m in self.data.values() for k in m.attrs.keys()))

    # MAPPINGS -----------------------------------------------
    @property
    def data(self) -> h5py.Group:
        """Return the '/data' group."""
        return super().__getitem__("data")

    @property
    def lookup(self) -> h5py.Group:
        """Return the '/lookup' group."""
        return super().__getitem__("lookup")

    def list_mappings(self) -> list[str]:
        """
        List all mappings in this file

        Returns:
        --------
        mappings : list
            List of the names of all mappings in the OMX file. Mappings
            are stored internally in the 'lookup' subset of the HDF5 file
            structure. Returns empty list if there are no mappings.
        """
        try:
            return list(self.lookup.keys())
        except KeyError:
            return []

    def delete_mapping(self, title) -> None:
        """
        Remove a mapping.

        Raises:
        -------
        LookupError : if the specified mapping does not exist.
        """
        try:
            del self.lookup[title]
            self.flush()
        except KeyError:
            raise LookupError(f"No such mapping: {title}")

    def delete_matrix(self, name) -> None:
        """
        Remove a matrix.

        Raises:
        -------
        LookupError : if the specified matrix does not exist.
        """
        try:
            del self.data[name]
            self.flush()
        except Exception:
            raise LookupError(f"No such matrix: {name}")

    def mapping(self, title) -> dict[Any, int]:
        """
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
        """
        entries = self.lookup[title][:]
        # build reverse key-lookup
        return {k: i for i, k in enumerate(entries)}

    def map_entries(self, title) -> list[Any]:
        """
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
        """
        return self.lookup[title][:].tolist()

    def create_mapping(self, title, entries, overwrite=False):
        """
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
        """

        # Enforce shape-checking
        if shape := self.shape():
            if len(entries) not in shape:
                raise ShapeError("Mapping must match one data dimension")

        existing = self.list_mappings()
        if title in existing:
            if overwrite:
                self.delete_mapping(title)
            else:
                raise LookupError(f"{title} mapping already exists.")

        # Ensure lookup group exists when writable and write the mapping
        return self.lookup.create_dataset(title, data=entries)

    # The following functions implement Python list/dictionary lookups. ----
    def __getitem__(self, key):
        """
        Return a matrix by name, a list of matrices by attributes, or a HDF5 group for given absolute path.
        """

        if isinstance(key, str):
            # It's not uncommon to want a way out of the omx object, so we provide a special assess method via a
            # path. Everything else is assumed to be in data
            if key.startswith("/"):
                return super().__getitem__(key)
            else:
                try:
                    return self.data[key]
                except KeyError:
                    raise LookupError(f"Key {key} not found")

        if not hasattr(key, "keys"):  # Pseudo isinstance(key, dict) check
            raise LookupError(f"Key {key} not found")

        # Loop through key/value pairs (attribute lookup)
        mats = list(self.values())
        for a in key.keys():
            mats = self._getMatricesByAttribute(a, key[a], mats)

        # Shadowed 'mats' variable means that the empty dict query (e.g. f[{}]) returns all children of data.
        return mats

    def _getMatricesByAttribute(self, key, value, matrices=None):
        """Return a matrix by name, or a list of matrices by attributes"""
        answer = []

        if matrices is None:
            matrices = list(self.values())

        for m in matrices:
            # Only test if key is present in matrix attributes
            if key in m.attrs and m.attrs[key] == value:
                answer.append(m)

        return answer

    def __len__(self):
        """Return the length of the '/data' group."""
        return len(self.data)

    def __setitem__(self, key, dataset):
        """
        Create a matrix with a given name.

        If a h5py.Dataset is provide that dataset is copied directly.
        """
        # We need to determine dtype and shape from the object that's been passed in.
        # This assumes 'dataset' is a numpy object.

        # Check if it's already a h5py dataset (copy?)
        if isinstance(dataset, h5py.Dataset):
            return self.data.copy(dataset, key)

        try:
            del self[key]
        except KeyError:
            # If the key does not exist yet, there's nothing to delete; this is expected.
            pass

        return self.create_matrix(key, obj=dataset)

    # Our set and get item methods break these methods from h5py. These could be useful so we restore them by forward
    # the call to the data group instead of the file object.
    def items(self):
        """Return the key value pairs of the '/data' group."""
        return self.data.items()

    def keys(self):
        """Return the keys of the '/data' group."""
        return self.data.keys()

    def values(self):
        """Return the values of the '/data' group."""
        return self.data.values()

    def __delitem__(self, key):
        """
        Delete a matrix by name, or a HDF5 group for given absolute path.
        """
        if key.startswith("/"):
            super().__delitem__(key)
        else:
            del self.data[key]

    def __iter__(self):
        """Iterate over the matrices in this container."""
        return iter(self.values())

    def __contains__(self, item):
        """Test if a name is with the '/data' group."""
        return item in self.data

    # BACKWARD COMPATIBILITY:
    createMapping = create_mapping
    createMatrix = create_matrix
    deleteMapping = delete_mapping
    listMatrices = list_matrices
    listAllAttributes = list_all_attributes
    listMappings = list_mappings
    mapentries = map_entries
    mapEntries = map_entries
