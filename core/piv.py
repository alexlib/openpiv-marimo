"""UI-agnostic PIV compute: pass config, single/multi-pass correlation.

No marimo import here on purpose — keep this reusable from a CLI or tests.
Falls back to a pure-numpy cross-correlation if openpiv is unavailable
(e.g. not yet resolvable as a Pyodide wheel), so the notebook still runs.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np

try:
    from openpiv.pyprocess import extended_search_area_piv as _openpiv_corr
    HAVE_OPENPIV = True
except Exception:
    HAVE_OPENPIV = False


@dataclass
class PassConfig:
    window_size: int = 64
    overlap: int = 32
    search_area: int = 64
    snr_threshold: float = 1.3
    interpolate_outliers: bool = True


@dataclass
class PivConfig:
    passes: list[PassConfig] = field(default_factory=lambda: [PassConfig()])

    @property
    def is_multi_pass(self) -> bool:
        return len(self.passes) > 1


def _fallback_corr(a, b, window_size, overlap, search_area):
    """Minimal single-pass normalized cross-correlation, numpy-only."""
    step = window_size - overlap
    ny = (a.shape[0] - window_size) // step + 1
    nx = (a.shape[1] - window_size) // step + 1
    u = np.zeros((ny, nx))
    v = np.zeros((ny, nx))
    for j in range(ny):
        for i in range(nx):
            y0, x0 = j * step, i * step
            ia = a[y0:y0 + window_size, x0:x0 + window_size]
            pad = (search_area - window_size) // 2
            y1, x1 = max(0, y0 - pad), max(0, x0 - pad)
            ib = b[y1:y1 + search_area, x1:x1 + search_area]
            if ib.shape[0] < window_size or ib.shape[1] < window_size:
                continue
            corr = np.array([
                [np.sum(ia * ib[dy:dy + window_size, dx:dx + window_size])
                 for dx in range(ib.shape[1] - window_size + 1)]
                for dy in range(ib.shape[0] - window_size + 1)
            ])
            peak = np.unravel_index(np.argmax(corr), corr.shape)
            center = ((corr.shape[0] - 1) / 2, (corr.shape[1] - 1) / 2)
            v[j, i] = peak[0] - center[0]
            u[j, i] = peak[1] - center[1]
    return u, v


def run_pass(frame_a: np.ndarray, frame_b: np.ndarray, cfg: PassConfig):
    """Run one PIV pass; returns (u, v) displacement fields."""
    if HAVE_OPENPIV:
        u, v, _ = _openpiv_corr(
            frame_a, frame_b,
            window_size=cfg.window_size,
            overlap=cfg.overlap,
            search_area_size=cfg.search_area,
        )
        return u, v
    return _fallback_corr(frame_a, frame_b, cfg.window_size, cfg.overlap, cfg.search_area)


def run_pipeline(frame_a: np.ndarray, frame_b: np.ndarray, config: PivConfig):
    """Run all configured passes in sequence. Later passes just re-run with
    their own window/search settings (predictor-field warping is a future
    upgrade, not needed for the boilerplate)."""
    results = []
    for cfg in config.passes:
        u, v = run_pass(frame_a, frame_b, cfg)
        results.append((cfg, u, v))
    return results
