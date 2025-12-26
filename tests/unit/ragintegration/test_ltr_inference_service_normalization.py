import numpy as np


def test_normalize_scores_minmax_basic() -> None:
    """Min-max normalization maps min->0, max->1 and preserves order."""
    from contexts.ragintegration.infrastructure.ml.inference_service import LTRInferenceService

    svc = LTRInferenceService(model_path=None)
    raw = np.array([1.0, 2.0, 3.0], dtype=float)
    norm = svc.normalize_scores_minmax(raw)

    assert norm.shape == raw.shape
    assert float(norm[0]) == 0.0
    assert float(norm[1]) == 0.5
    assert float(norm[2]) == 1.0


def test_normalize_scores_minmax_constant_defaults_to_half() -> None:
    """When all scores are equal, normalization returns a neutral default."""
    from contexts.ragintegration.infrastructure.ml.inference_service import LTRInferenceService

    svc = LTRInferenceService(model_path=None)
    raw = np.array([5.0, 5.0, 5.0], dtype=float)
    norm = svc.normalize_scores_minmax(raw, default=0.5)

    assert np.allclose(norm, np.array([0.5, 0.5, 0.5], dtype=float))


def test_normalize_scores_minmax_handles_non_finite() -> None:
    """Non-finite values are replaced with the default and do not break normalization."""
    from contexts.ragintegration.infrastructure.ml.inference_service import LTRInferenceService

    svc = LTRInferenceService(model_path=None)
    raw = np.array([np.nan, 10.0, np.inf, -5.0], dtype=float)
    norm = svc.normalize_scores_minmax(raw, default=0.5)

    # All outputs should be finite and in [0, 1]
    assert np.isfinite(norm).all()
    assert (norm >= 0.0).all() and (norm <= 1.0).all()


