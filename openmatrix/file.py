import numpy as np
import h5py

from .exceptions import ShapeError


class File(h5py.File):
    """
    OMX File class, which contains all the methods for adding, removing, manipulating matrices
    and mappings in an OMX file.
    """

    def __init__(self, name, mode="r", title="", **kwargs):
        super(File, self).__init__(name, mode, **kwargs)
        self._shape = None

    def version(self):
        """
        Return the OMX file format of this OMX file, embedded in the OMX_VERSION file attribute.
        Returns None if the OMX_VERSION attribute is not set.
        """
        if "OMX_VERSION" in self.attrs:
            return self.attrs["OMX_VERSION"]
        else:
            return None

    def create_matrix(self, name, shape=None, title="", filters=None, chunks=True, obj=None, dtype=None, attrs=None):
        """
        Create an OMX Matrix (Dataset) at the root level. User must pass in either
        an existing numpy matrix, or a shape and a dtype.
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
        compression = None
        compression_opts = None
        shuffle = False

        # If filters is passed (it might be a tables.Filters object or a dict or None)
        # We'll try to parse basic stuff or just use defaults if it's the standard OMX one
        if filters:
            if hasattr(filters, "complib"):
                if filters.complib == "zlib":
                    compression = "gzip"
                elif filters.complib:
                    compression = filters.complib

                if hasattr(filters, "complevel"):
                    compression_opts = filters.complevel
                if hasattr(filters, "shuffle"):
                    shuffle = filters.shuffle

        # Defaults if not specified but standard in OMX (zlib 1)
        # Actually tables default in __init__ was passed.
        # h5py doesn't have a default file-wide filter.
        # We'll rely on what's passed or defaults.

        # Create 'data' group if it doesn't exist
        if not super(File, self).__contains__("data"):
            self.create_group("data")

        # create_dataset arguments
        kwargs = {}
        if compression:
            kwargs["compression"] = compression
        if compression_opts is not None:
            kwargs["compression_opts"] = compression_opts
        if shuffle:
            kwargs["shuffle"] = shuffle
        if chunks:
            kwargs["chunks"] = chunks

        matrix = (
            super(File, self).__getitem__("data").create_dataset(name, shape=dshape, dtype=dtype, data=data, **kwargs)
        )

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

    def shape(self):
        """
        Get the one and only shape of all matrices in this File
        """

        # If we already have the shape, just return it
        if self._shape:
            return self._shape

        # If shape is already set in root node attributes, grab it
        if "SHAPE" in self.attrs:
            # Shape is stored as a numpy.array:
            arrayshape = self.attrs["SHAPE"]
            # which must be converted to a tuple:
            realshape = (arrayshape[0], arrayshape[1])
            self._shape = realshape
            return self._shape

        # Inspect the first Dataset object to determine its shape
        if super(File, self).__contains__("data"):
            data_group = super(File, self).__getitem__("data")
            if len(data_group) > 0:
                # Get first key
                first_key = list(data_group.keys())[0]
                self._shape = data_group[first_key].shape

                # Store it if we can
                if self.mode != "r":
                    storeshape = np.array([self._shape[0], self._shape[1]], dtype="int32")
                    self.attrs["SHAPE"] = storeshape

                return self._shape
        return None

    def list_matrices(self):
        """
        List the matrix names in this File
        """
        if super(File, self).__contains__("data"):
            return list(super(File, self).__getitem__("data").keys())
        return []

    def list_all_attributes(self):
        """
        Return set of all attributes used for any Matrix in this File
        """
        all_tags = set()
        if super(File, self).__contains__("data"):
            data_group = super(File, self).__getitem__("data")
            for m_name in data_group:
                m = data_group[m_name]
                all_tags.update(m.attrs.keys())
        return sorted(list(all_tags))

    # MAPPINGS -----------------------------------------------
    def list_mappings(self):
        """
        List all mappings in this file
        """
        if super(File, self).__contains__("lookup"):
            return list(super(File, self).__getitem__("lookup").keys())

        return []

    def delete_mapping(self, title):
        """
        Remove a mapping.
        """
        try:
            lookup = super(File, self).__getitem__("lookup")
            del lookup[title]
        except Exception:
            raise LookupError(f"No such mapping: {title}")

    def mapping(self, title):
        """
        Return dict containing key:value pairs for specified mapping.
        """
        try:
            # fetch entries
            if not super(File, self).__contains__("lookup"):
                raise LookupError(f"No such mapping: {title}")

            lookup = super(File, self).__getitem__("lookup")
            if title not in lookup:
                raise LookupError(f"No such mapping: {title}")

            entries = lookup[title][:]

            # build reverse key-lookup
            keymap = {}
            for i in range(len(entries)):
                keymap[entries[i]] = i

            return keymap

        except Exception as e:
            if isinstance(e, LookupError):
                raise e
            raise LookupError(f"No such mapping: {title}")

    def map_entries(self, title):
        """Return a list of entries for the specified mapping."""
        try:
            if not super(File, self).__contains__("lookup"):
                raise LookupError(f"No such mapping: {title}")

            lookup = super(File, self).__getitem__("lookup")
            if title not in lookup:
                raise LookupError(f"No such mapping: {title}")

            entries = lookup[title][:]
            # Convert to list if it's a numpy array
            if hasattr(entries, "tolist"):
                return entries.tolist()
            return entries

        except Exception as e:
            if isinstance(e, LookupError):
                raise e
            raise LookupError(f"No such mapping: {title}")

    def create_mapping(self, title, entries, overwrite=False):
        """
        Create an equivalency index.
        """

        # Enforce shape-checking
        if self.shape():
            if len(entries) not in self._shape:
                raise ShapeError("Mapping must match one data dimension")

        # Handle case where mapping already exists:
        existing = self.list_mappings()
        if title in existing:
            if overwrite:
                self.delete_mapping(title)
            else:
                raise LookupError(f"{title} mapping already exists.")

        # Create lookup group under root if it doesn't already exist.
        if not super(File, self).__contains__("lookup"):
            self.create_group("lookup")

        # Write the mapping!
        lookup = super(File, self).__getitem__("lookup")
        mymap = lookup.create_dataset(title, data=entries)

        return mymap

    # The following functions implement Python list/dictionary lookups. ----
    def __getitem__(self, key):
        """Return a matrix by name, or a list of matrices by attributes"""

        if isinstance(key, str):
            # Direct access to data/lookup or paths
            if key in ["data", "lookup"] or key.startswith("/"):
                return super(File, self).__getitem__(key)

            # Check inside 'data' group
            if super(File, self).__contains__("data"):
                data_group = super(File, self).__getitem__("data")
                if key in data_group:
                    return data_group[key]

            if super(File, self).__contains__(key):
                return super(File, self).__getitem__(key)

            # If not found
            raise LookupError(f"Key {key} not found")

        if "keys" not in dir(key):
            raise LookupError(f"Key {key} not found")

        # Loop through key/value pairs (attribute lookup)
        mats = []
        if super(File, self).__contains__("data"):
            data_group = super(File, self).__getitem__("data")
            mats = [data_group[n] for n in data_group]

        for a in key.keys():
            mats = self._getMatricesByAttribute(a, key[a], mats)

        return mats

    def _getMatricesByAttribute(self, key, value, matrices=None):

        answer = []

        if matrices is None:
            if super(File, self).__contains__("data"):
                data_group = super(File, self).__getitem__("data")
                matrices = [data_group[n] for n in data_group]
            else:
                matrices = []

        for m in matrices:
            if m.attrs is None:
                continue

            # Only test if key is present in matrix attributes
            if key in m.attrs and m.attrs[key] == value:
                answer.append(m)

        return answer

    def __len__(self):
        if super(File, self).__contains__("data"):
            return len(super(File, self).__getitem__("data"))
        return 0

    def __setitem__(self, key, dataset):
        # We need to determine atom and shape from the object that's been passed in.
        # This assumes 'dataset' is a numpy object.

        # Check if it's already an h5py dataset (copy?)
        if isinstance(dataset, h5py.Dataset):
            # Copying datasets across files or within file is supported in h5py
            # dest path: /data/key
            if not super(File, self).__contains__("data"):
                self.create_group("data")

            # Implement internal logic or just use assignment if we supported it
            # But here we want to use create_matrix logic to enforce shapes etc?
            pass

        # Remove if exists
        if super(File, self).__contains__("data"):
            data_group = super(File, self).__getitem__("data")
            if key in data_group:
                del data_group[key]

        return self.create_matrix(key, obj=dataset)

    def __delitem__(self, key):
        if super(File, self).__contains__("data"):
            data_group = super(File, self).__getitem__("data")
            if key in data_group:
                del data_group[key]
                return

        # Try standard delete
        try:
            super(File, self).__delitem__(key)
        except Exception:
            pass

    def __iter__(self):
        """Iterate over the keys in this container"""
        if super(File, self).__contains__("data"):
            data_group = super(File, self).__getitem__("data")
            for name in data_group:
                yield data_group[name]
        else:
            return iter([])

    def __contains__(self, item):
        if super(File, self).__contains__("data"):
            data_group = super(File, self).__getitem__("data")
            return item in data_group
        return False

    # BACKWARD COMPATIBILITY:
    createMapping = create_mapping
    createMatrix = create_matrix
    deleteMapping = delete_mapping
    listMatrices = list_matrices
    listAllAttributes = list_all_attributes
    listMappings = list_mappings
    mapentries = map_entries
    mapEntries = map_entries
