from PySide6.QtCore import QObject
from numpy.typing import NDArray
from typing import Any
import cv2
import itertools
import numpy as np


def resize_by_ratio(image: NDArray[Any], ratio: float) -> NDArray[Any]:
    """
    Provided a fractional ratio in the form of a floating point number, resize
    the image dimensions (width, height) by scaling each axis by the ratio.
    Note this does not include axes outside of the realm of width and height
    and the procedure assumes the axes are ordered as (height, width,
    a,b,c,...).

    Understand any fractional portions of the new resulting axes will be
    truncated and no rounding will occur.

    Example: Specifying `ratio=0.5` will halve each axis (height, width) and
    thus return an image 25% of the original size.

    :param image: ndarray encoded image
    :param ratio: a positive floating point number representing the resize ratio
    """
    shape = image.shape[:2]
    nshape = np.array(shape, dtype=np.float32) * ratio
    nshape = nshape.astype(np.uint64)  # truncate to integer
    nshape = tuple(itertools.chain.from_iterable(nshape))
    return np.asarray(cv2.resize(image, nshape[::-1], interpolation=cv2.INTER_CUBIC))


def normalize_minmax(data: NDArray[Any]):
    """
    Applies min max norm to an NDArray
    There isn't much else to say.
    """
    epsilon = 1e-17
    d = data.astype(np.float32)
    dmin, dmax = d.min(), d.max()
    drange = dmax - dmin
    return (d - dmin) / (drange + epsilon)


def norm_uint8(ndarray: NDArray) -> NDArray[np.uint8]:
    """
    Re-center the data between zero and one and then convert to 8-bit unsigned
    integers after a scaling operation.

    :param ndarray: any contiguous memory collection of ndarray encoded data
    """
    intermediates = normalize_minmax(ndarray)
    return (255 * intermediates).astype(np.uint8)


def find_children_of_types(parent: QObject, *classes: type) -> dict[type, list[QObject]]:
    """
    WARNING: MADE BY THE CHATBOT
    Recursively traverse the QObject tree and collect instances of specified classes.

    :param parent: The parent QObject to start the search from.
    :type parent: QObject
    :param classes: Variable number of QObject subclasses to search for.
    :return: A dictionary where keys are class types and values are lists of instances satisfying the filter.
    """
    cached_children: dict[type, list[QObject]] = {cls: [] for cls in classes}

    def traverse(obj: QObject):
        for child in obj.children():
            for cls in classes:
                if isinstance(child, cls):
                    cached_children[cls].append(child)
            traverse(child)

    traverse(parent)
    return cached_children


def merge_cached_nodes(cached_list: list[dict[type, list[QObject]]]) -> dict[type, list[QObject]]:
    """
    WARNING: MADE BY THE CHATBOT
    Merge multiple cached dictionaries into a single dictionary.

    :param cached_list: A list of cached dictionaries to merge.
    :return: A single dictionary with aggregated lists of instances.

    :Example:

        >>> merged = merge_cached_children([cached1, cached2, cached3])
        >>> for cls, instances in merged.items():
        >>>     print(f"Total {cls.__name__} instances: {len(instances)}")
    """
    merged: dict[type, list[QObject]] = {}

    for cached in cached_list:
        for cls, instances in cached.items():
            if cls not in merged:
                merged[cls] = []
            merged[cls].extend(instances)

    return merged
