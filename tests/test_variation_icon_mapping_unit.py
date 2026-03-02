"""
Tiny unit test for the variation icon mapping.

This is deliberately "dumb" and explicit:
if someone changes icon filenames or statuses,
this test should fail and force an intentional update.
"""

from mdcspc.metric_config import VARIATION_ICON_FILES, VariationStatus

def test_variation_icon_files_expected_filenames_and_statuses():
    """
    Check that VARIATION_ICON_FILES exactly matches the expected mapping
    from VariationStatus -> icon filename.

    If you change icon filenames or add/remove statuses, update this test
    *and* the assets/icons folder deliberately.
    """
    # Expected mapping keyed by the Enum's .value (strings like "improvement_high")
    expected_by_value = {
        "common_cause": "VariationIconCommonCause.png",
        "improvement_high": "VariationIconImprovementHigh.png",
        "improvement_low": "VariationIconImprovementLow.png",
        "concern_high": "VariationIconConcernHigh.png",
        "concern_low": "VariationIconConcernLow.png",
        "neither_high": "VariationIconNeitherHigh.png",
        "neither_low": "VariationIconNeitherLow.png",
    }

    # Re-key the actual mapping by status.value so we don't depend on Enum member names
    actual_by_value = {
        status.value: filename
        for status, filename in VARIATION_ICON_FILES.items()
    }

    # 1) Same keys (no missing / extra statuses)
    assert set(actual_by_value.keys()) == set(
        expected_by_value.keys()
    ), f"Status set mismatch. Expected {set(expected_by_value)}, got {set(actual_by_value)}"

    # 2) Exact filename matches
    for status_value, expected_filename in expected_by_value.items():
        actual_filename = actual_by_value[status_value]
        assert actual_filename == expected_filename, (
            f"Icon filename mismatch for status {status_value!r}: "
            f"expected {expected_filename!r}, got {actual_filename!r}"
        )

    # 3) Sanity: no duplicate filenames mapped to different statuses
    filenames = list(actual_by_value.values())
    assert len(filenames) == len(set(filenames)), (
        "Duplicate icon filenames detected in VARIATION_ICON_FILES mapping; "
        "each status should have a distinct icon."
    )
