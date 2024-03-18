"""
Check if input text is sensitive - at the moment testing for potentially personal data.

To start - chosen a small spaCy model and some fairly generic settings.
To improve the results - may change the settings for the analyzer engine.
"""

import re

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider

# https://microsoft.github.io/presidio/supported_entities/
UK_POSTAL_CODE_REGEX = r"[A-Z]{1,2}[0-9R][0-9A-Z]? ?[0-9][ABD-HJLNP-UW-Z]{2}"
UK_MOBILE_PHONE_REGEX = r"(\+44\s?|\(?0\)?)7\d{3}\s?\d{3}\s?\d{3}"
UK_LANDLINE_REGEX = r"(\+44\s?)?\(?0?\)?[1,2,3]\d{2,3}\s?\d{0,2}\)?\s?\d{6}"
SENSITIVITY_MARKINGS = ["SECRET", "OFFICIAL SENSITIVE", "OFFICIAL-SENSITIVE"]
SCORE_THRESHOLDS = {
    "EMAIL_ADDRESS": 0.7,
    "PERSON": 0.7,
    "PHONE_NUMBER": 0.7,
    "UK_POSTCODE": 1.0,
    "SENSITIVITY_MARKINGS": 1.0,
    "UK_MOBILE_PHONE_REGEX": 1.0,
    "UK_LANDLINE_REGEX": 1.0,
}  # All the entities to include


def get_analyzer_engine():
    configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
    }
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_eng_spacy_engine = provider.create_engine()
    analyzer_engine = AnalyzerEngine(nlp_engine=nlp_eng_spacy_engine, supported_languages=["en"])
    # Add some regex patterns
    sensitivity_markings_recognizer = PatternRecognizer(
        supported_entity="SENSITIVITY_MARKINGS", deny_list=SENSITIVITY_MARKINGS, global_regex_flags=re.IGNORECASE
    )
    uk_postcode_pattern = Pattern(name="uk_postcode_pattern", regex=UK_POSTAL_CODE_REGEX, score=1.0)
    uk_postcode_recognizer = PatternRecognizer(
        supported_entity="UK_POSTCODE", patterns=[uk_postcode_pattern], global_regex_flags=re.IGNORECASE
    )
    # More patterns for UK phone numbers (not exhaustive, should cover most personal numbers)
    uk_mobile_pattern = Pattern(name="uk_mobile_pattern", regex=UK_MOBILE_PHONE_REGEX, score=1.0)
    uk_mobile_recognizer = PatternRecognizer(supported_entity="UK_MOBILE_PHONE_REGEX", patterns=[uk_mobile_pattern])
    uk_landline_pattern = Pattern(name="uk_landline_pattern", regex=UK_LANDLINE_REGEX, score=1.0)
    uk_landline_recognizer = PatternRecognizer(supported_entity="UK_LANDLINE_REGEX", patterns=[uk_landline_pattern])
    # Add all regex patterns to analyser engine (on top of names & defaults)
    analyzer_engine.registry.add_recognizer(sensitivity_markings_recognizer)
    analyzer_engine.registry.add_recognizer(uk_postcode_recognizer)
    analyzer_engine.registry.add_recognizer(uk_mobile_recognizer)
    analyzer_engine.registry.add_recognizer(uk_landline_recognizer)
    return analyzer_engine


ask_ai_analyzer_engine = get_analyzer_engine()


def analyze_text(input_text: str) -> list:
    analyser_results = ask_ai_analyzer_engine.analyze(text=input_text, language="en", entities=SCORE_THRESHOLDS.keys())
    return analyser_results


def get_analyser_results_above_thresholds(analyser_results: list) -> list:
    sensitive_results = [result for result in analyser_results if result.score >= SCORE_THRESHOLDS[result.entity_type]]
    return sensitive_results


def is_text_potentially_sensitive(input_text: str) -> bool:
    analyser_results = analyze_text(input_text)
    sensitive_results = get_analyser_results_above_thresholds(analyser_results)
    return len(sensitive_results) > 0
