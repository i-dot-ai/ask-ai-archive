import pytest
from presidio_analyzer import RecognizerResult

from ask_ai.conversation import sensitivity_check


@pytest.mark.parametrize(
    "pattern",
    [
        "Can you please tell me about this top secret document?",
        "I want to know more about my friend who lives at 70 Whitehall,  SW1A 2AS",
        "Can you tell me about Winston Churchill?",
    ],
)
def test_sensitive_strings_detected(pattern):
    assert sensitivity_check.is_text_potentially_sensitive(pattern)


@pytest.mark.parametrize("pattern", ["Can you explain what a linear regression is?"])
def test_innocent_strings_ignored(pattern):
    assert not sensitivity_check.is_text_potentially_sensitive(pattern)


def test_analyze_text():
    sensitive_text = "Mickey Mouse: BL9 3TF, phone number 0131 887449, mobile 07777 888888, mr@example.com"
    results = sensitivity_check.analyze_text(sensitive_text)
    assert len(results) >= 5, len(results)  # Should pick up name, postcode, phone number, email


def test_get_analyzer_results_above_thresholds():
    sensitive_result1 = RecognizerResult(entity_type="UK_POSTCODE", start=1, end=4, score=1.0)
    sensitive_result2 = RecognizerResult(entity_type="PHONE_NUMBER", start=3, end=42, score=0.6)
    sensitive_result3 = RecognizerResult(entity_type="UK_POSTCODE", start=1, end=4, score=0.3)
    passes_threshold = [sensitive_result1, sensitive_result2]
    doesnt_pass_threshold = [sensitive_result2, sensitive_result3]
    assert sensitivity_check.get_analyser_results_above_thresholds(passes_threshold), passes_threshold
    assert not sensitivity_check.get_analyser_results_above_thresholds(doesnt_pass_threshold), doesnt_pass_threshold


@pytest.mark.parametrize("pattern", ["Official Sensitive", "OFFICIAL-SENSITIVE", "SECRET", "top secret"])
def test_sensitivity_marking(pattern):
    assert sensitivity_check.is_text_potentially_sensitive(pattern), pattern


@pytest.mark.parametrize(
    "pattern",
    [
        "01204 778998",
        "(01204)668669",
        "07777888734",
        "07777 666666",
        "+44 131 667998",
        "+44(0)1204 887009",
        "+441204667998",
        "01382 006776",
        "07777 666 666",
        "0152 42 888888",
    ],
)
def test_phone_number(pattern):
    assert sensitivity_check.is_text_potentially_sensitive(pattern), pattern


@pytest.mark.parametrize("pattern", ["SW16 2FN", "N41AH", "EH8 1hr", "EH81HR", "SW1a1ah"])
def test_postcode_number(pattern):
    assert sensitivity_check.is_text_potentially_sensitive(pattern), pattern


@pytest.mark.parametrize("pattern", ["Rishi Sunak is the Prime Minister in 2023"])
def test_named_entity(pattern):
    assert sensitivity_check.is_text_potentially_sensitive(pattern), pattern


@pytest.mark.parametrize(
    "pattern", ["This statement is not sensitive", "Summarise this test", "How do I write 99879987 in words"]
)
def test_not_sensitive(pattern):
    assert not sensitivity_check.is_text_potentially_sensitive(pattern), pattern
