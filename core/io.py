"""Image loading — works identically under native Python and Pyodide/WASM.

Both paths return raw bytes; nothing here touches the local filesystem
directly or any cloud SDK, so it runs the same in-browser or on a server.
"""
from __future__ import annotations
import io
import numpy as np
from PIL import Image


def bytes_to_gray_array(data: bytes) -> np.ndarray:
    """Decode image bytes (PNG/TIFF/JPEG) to a 2D float32 grayscale array."""
    img = Image.open(io.BytesIO(data)).convert("F")
    return np.asarray(img, dtype=np.float32)


def load_from_upload(upload_value) -> dict[str, np.ndarray]:
    """upload_value: the .value of a mo.ui.file() element (list of UploadedFile)."""
    return {f.name: bytes_to_gray_array(f.contents) for f in upload_value}


def load_from_url(url: str) -> np.ndarray:
    """Fetch a single image from a public/signed URL (e.g. a GCS object URL).

    Uses urllib so it works both natively and under Pyodide's patched
    networking (marimo/Pyodide route stdlib HTTP through the browser fetch API).
    """
    from urllib.request import urlopen
    with urlopen(url) as resp:
        data = resp.read()
    return bytes_to_gray_array(data)
