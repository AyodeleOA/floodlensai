from __future__ import annotations

from typing import Any

try:
    import h3
    H3_AVAILABLE = True
except ImportError:
    H3_AVAILABLE = False


def assign_to_grid_cell(lat: float, lng: float, resolution: int = 8) -> str:
    """Assign a coordinate to an H3 grid cell.

    Returns the H3 cell index as a string.
    Falls back to a simple lat/lng bucket if h3 is not available.
    """
    if H3_AVAILABLE:
        return h3.latlng_to_cell(lat, lng, resolution)

    # Fallback: simple grid bucket
    grid_lat = round(lat * (10 ** resolution)) // 1
    grid_lng = round(lng * (10 ** resolution)) // 1
    return f"grid_{grid_lat}_{grid_lng}"


def get_cell_center(cell_index: str) -> tuple[float, float]:
    """Get the center coordinates of a grid cell."""
    if H3_AVAILABLE and not cell_index.startswith("grid_"):
        lat, lng = h3.cell_to_latlng(cell_index)
        return lat, lng

    # Fallback parsing
    if cell_index.startswith("grid_"):
        parts = cell_index.split("_")
        grid_lat = int(parts[1])
        grid_lng = int(parts[2])
        return grid_lat / (10 ** 8), grid_lng / (10 ** 8)
    return 0.0, 0.0


def get_cell_boundary(cell_index: str) -> list[tuple[float, float]]:
    """Get the boundary polygon of a grid cell as a list of (lat, lng) pairs."""
    if H3_AVAILABLE and not cell_index.startswith("grid_"):
        boundary = h3.cell_to_boundary(cell_index)
        return [(lat, lng) for lat, lng in boundary]

    # Fallback: return a small square around the center
    lat, lng = get_cell_center(cell_index)
    size = 0.001
    return [
        (lat - size, lng - size),
        (lat - size, lng + size),
        (lat + size, lng + size),
        (lat + size, lng - size),
        (lat - size, lng - size),
    ]


def get_cells_in_bbox(
    min_lon: float, min_lat: float, max_lon: float, max_lat: float, resolution: int = 8
) -> list[str]:
    """Get all grid cells within a bounding box."""
    if H3_AVAILABLE:
        # Use h3.polyfill with the bbox as a polygon
        polygon = [
            (min_lat, min_lon),
            (min_lat, max_lon),
            (max_lat, max_lon),
            (max_lat, min_lon),
            (min_lat, min_lon),
        ]
        try:
            cells = h3.polygon_to_cells(polygon, resolution)
            return list(cells)
        except Exception:
            pass

    # Fallback: generate a coarse grid
    cells = []
    step = 0.01
    lat = min_lat
    while lat <= max_lat:
        lng = min_lon
        while lng <= max_lon:
            cells.append(assign_to_grid_cell(lat, lng, resolution))
            lng += step
        lat += step
    return cells


def get_neighbouring_cells(cell_index: str, resolution: int = 8) -> list[str]:
    """Get the neighbouring cells of a given cell."""
    if H3_AVAILABLE and not cell_index.startswith("grid_"):
        try:
            return list(h3.grid_disk(cell_index, 1))
        except Exception:
            pass
    return []
