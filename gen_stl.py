from __future__ import annotations

import hashlib
import pathlib
from typing import Tuple

import numpy as np
import trimesh

__all__ = [
    "smooth_radii",
    "radii_to_stl",
]


def smooth_radii(
    r: np.ndarray,
    dz: float = 0.002,
    res: int = 5,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return a *smoothed* and *densified* radius/height profile.

    Parameters
    ----------
    r
        1‑D array of radii in **metres**.
    dz
        Original slice height in metres.
    res
        How many dense points to create **per** original slice.
    """
    try:
        from scipy.interpolate import CubicSpline  # heavy but C²‑smooth

        z = np.arange(r.size, dtype=float) * dz
        cs = CubicSpline(z, r, bc_type="natural")
        z_dense = np.linspace(0.0, z[-1], r.size * res)
        r_dense = cs(z_dense)
    except ModuleNotFoundError:  # fall back to a cheap smoother
        z_dense = np.repeat(np.arange(r.size) * dz, res)
        r_dense = np.repeat(r, res)
        r_dense = np.convolve(r_dense, [0.25, 0.5, 0.25], mode="same")

    return np.clip(r_dense, 0.0, None), z_dense


# ---------------------------------------------------------------------------
#  Main helper – radiate + STL export
# ---------------------------------------------------------------------------

def radii_to_stl(
    r: np.ndarray,
    dz: float = 0.002,
    res: int = 5,
    stl_path: str | pathlib.Path = "shape.stl",
) -> Tuple[pathlib.Path, str]:
    """Convert *radii → STL* and return *(path, MD5 hash)*.

    The MD5 is computed on the vertex buffer so GA can cache identical
    geometries quickly.
    """
    r = np.asarray(r, dtype=float)
    r_s, z_s = smooth_radii(r, dz=dz, res=res)

    # Build 2‑D profile in XZ‑plane and close it on the axis
    profile = np.column_stack([r_s, z_s])
    profile = np.vstack([[0.0, 0.0], profile, [0.0, z_s[-1]]])

    # Revolve 360° about Z‑axis (Trimesh ≤ 4.x)
    mesh = trimesh.creation.revolve(profile)

    # --- Repairs to ensure watertight STL -----------------------------------
    trimesh.repair.fill_holes(mesh)       # cover any open rims
    mesh.remove_duplicate_faces()
    mesh.fix_normals()                    # correct orientation

    mesh.export(str(stl_path))

    # Hash on *vertex* float buffer (faster than STL bytes)
    h = hashlib.md5(mesh.vertices.view(np.float64)).hexdigest()
    return pathlib.Path(stl_path), h
