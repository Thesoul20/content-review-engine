from content_review_engine.core.models import ReviewProfile
from content_review_engine.rules import check_forbidden_terms


def test_forbidden_terms_single_match_returns_finding() -> None:
    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
        forbidden_terms=["保证赚钱", "绝对安全"],
    )

    findings = check_forbidden_terms("这篇文章承诺保证赚钱。", profile)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "forbidden_terms"
    assert finding.severity == "warning"
    assert finding.message == "发现风险词：保证赚钱"
    assert finding.matched_term == "保证赚钱"
    assert finding.matched_text == "保证赚钱"


def test_forbidden_terms_no_match_returns_empty_list() -> None:
    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
        forbidden_terms=["保证赚钱", "绝对安全"],
    )

    findings = check_forbidden_terms("这篇文章只是在说明产品特点。", profile)

    assert findings == []


def test_forbidden_terms_multiple_matches_returns_multiple_findings() -> None:
    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
        forbidden_terms=["绝对安全", "保证赚钱", "100%有效"],
    )

    findings = check_forbidden_terms("这里写着绝对安全，也承诺保证赚钱，而且说自己100%有效。", profile)

    assert [finding.matched_term for finding in findings] == [
        "绝对安全",
        "保证赚钱",
        "100%有效",
    ]


def test_forbidden_terms_empty_configuration_returns_empty_list() -> None:
    profile = ReviewProfile(name="wechat", target_platform="wechat", forbidden_terms=[])

    findings = check_forbidden_terms("任何文本都不会触发。", profile)

    assert findings == []
