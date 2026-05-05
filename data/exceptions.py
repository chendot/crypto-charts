"""Exception types used by the data layer."""

from __future__ import annotations


class DataLayerError(Exception):
    """Base class for data-layer failures."""


class DataFetchError(DataLayerError):
    """Raised when a remote or local source cannot be fetched."""


class DataCacheError(DataLayerError):
    """Raised when cached data cannot be read or written."""


class DataSchemaError(DataLayerError):
    """Raised when normalized data does not match the expected schema."""
