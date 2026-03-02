# tests/test_assurance_icon_mapping_unit.py

from mdcspc.metric_config import (
    AssuranceStatus,
    ASSURANCE_ICON_FILES,
    classify_assurance_from_key,
)


def test_assurance_status_enum_members_exist():
    """
    Guardrail: ensure the AssuranceStatus enum retains the expected members.
    """
    assert AssuranceStatus.PASSING.value == "passing"
    assert AssuranceStatus.HIT_OR_MISS.value == "hit_or_miss"
    assert AssuranceStatus.FAILING.value == "failing"
    assert AssuranceStatus.NO_TARGET.value == "no_target"


def test_assurance_icon_files_mapping_is_complete_and_exact():
    """
    Guardrail: ensure every AssuranceStatus has an icon filename
    and the filenames match the canonical expected set.
    """
    expected = {
        AssuranceStatus.PASSING: "AssuranceIconPass.png",
        AssuranceStatus.HIT_OR_MISS: "AssuranceIconHitOrMiss.png",
        AssuranceStatus.FAILING: "AssuranceIconFail.png",
        AssuranceStatus.NO_TARGET: "IconEmpty.png",
    }

    # Same keys
    assert set(ASSURANCE_ICON_FILES.keys()) == set(expected.keys())

    # Exact filenames
    for status, filename in expected.items():
        assert ASSURANCE_ICON_FILES[status] == filename


def test_classify_assurance_from_key_maps_expected_keys():
    """
    Ensure SPC-layer assurance_key values map to the correct status + icon.
    """
    cases = [
        ("pass", AssuranceStatus.PASSING, "AssuranceIconPass.png"),
        ("fail", AssuranceStatus.FAILING, "AssuranceIconFail.png"),
        ("no_strong_assurance", AssuranceStatus.HIT_OR_MISS, "AssuranceIconHitOrMiss.png"),
        ("", AssuranceStatus.NO_TARGET, "IconEmpty.png"),
        ("no_data", AssuranceStatus.NO_TARGET, "IconEmpty.png"),
        ("unknown_key_should_fall_back", AssuranceStatus.NO_TARGET, "IconEmpty.png"),
        (None, AssuranceStatus.NO_TARGET, "IconEmpty.png"),
    ]

    for key, exp_status, exp_icon in cases:
        status, icon = classify_assurance_from_key(assurance_key=key, metric_cfg=None)
        assert status == exp_status
        assert icon == exp_icon
