"""
Serialization utilities for cache implementations.
"""

import logging
import msgpack
from typing import Any, Optional

# Configure logging
logger = logging.getLogger("mcp_server.cache.serialization")


def serialize(value: Any) -> Optional[bytes]:
    """
    Serialize a value to bytes using msgpack.

    Args:
        value: Value to serialize

    Returns:
        Serialized value as bytes or None if serialization fails
    """
    try:
        if isinstance(value, (dict, list, tuple)) and not isinstance(value, bytes):
            return msgpack.packb(value, use_bin_type=True)
        return value
    except Exception as e:
        logger.error(f"Error serializing value: {str(e)}")
        return None


def deserialize(value: Any) -> Any:
    """
    Deserialize a value from bytes using msgpack.

    Args:
        value: Value to deserialize

    Returns:
        Deserialized value or original value if deserialization fails
    """
    if not isinstance(value, bytes):
        return value
        
    try:
        return msgpack.unpackb(value, raw=False)
    except Exception as e:
        logger.error(f"Error deserializing value: {str(e)}")
        return value
