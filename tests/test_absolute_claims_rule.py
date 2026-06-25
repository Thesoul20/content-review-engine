from content_review_engine.core.models import ReviewProfile
from content_review_engine.rules import check_absolute_claims


def test_absolute_claims_detects_configured_term_with_severity_and_suggestion() -> None:
    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
        absolute_claims_terms=["全网最强", "永久有效"],
        absolute_claims_severity="error",
    )

    findings = check_absolute_claims("这是一款全网最强的内容审计工具。", profile)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "absolute_claims"
    assert finding.severity == "error"
    assert finding.message == "发现可能存在绝对化表述：全网最强"
    assert finding.suggestion is not None
    assert "更审慎的表述" in finding.suggestion
    assert finding.matched_term == "全网最强"
    assert finding.matched_text == "全网最强"
    assert finding.location is not None
    assert finding.location.start_line == 1
    assert finding.location.start_column == 5


def test_absolute_claims_returns_empty_list_when_no_terms_match() -> None:
    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
        absolute_claims_terms=["全网最强"],
    )

    findings = check_absolute_claims("这里没有夸大承诺。", profile)

    assert findings == []


def test_absolute_claims_allow_terms_suppresses_exact_term() -> None:
    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
        absolute_claims_terms=["全网最强", "永久有效"],
        absolute_claims_allow_terms=["永久有效"],
    )

    findings = check_absolute_claims("这里写着永久有效，也写着全网最强。", profile)

    assert [finding.matched_term for finding in findings] == ["全网最强"]


def test_absolute_claims_multiple_terms_return_multiple_findings() -> None:
    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
        absolute_claims_terms=["全网最强", "零风险"],
    )

    findings = check_absolute_claims("这款产品号称全网最强，而且零风险。", profile)

    assert [finding.matched_term for finding in findings] == ["全网最强", "零风险"]
