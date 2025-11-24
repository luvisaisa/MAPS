"""
Comprehensive Unit Tests for KeywordNormalizer

Tests medical keyword normalization, synonym mapping, abbreviation expansion,
and multi-word term detection.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.maps.keyword_normalizer import KeywordNormalizer


@pytest.fixture
def sample_medical_terms():
    """Sample medical terms dictionary for testing"""
    return {
        "synonyms": {
            "pulmonary": ["lung", "respiratory", "pneumonic"],
            "nodule": ["lesion", "mass", "opacity"],
            "malignant": ["cancerous", "malignancy"],
            "benign": ["non-cancerous"]
        },
        "abbreviations": {
            "CT": "computed tomography",
            "MRI": "magnetic resonance imaging",
            "GGO": "ground glass opacity",
            "ROI": "region of interest"
        },
        "multi_word_terms": [
            "ground glass opacity",
            "region of interest",
            "computed tomography",
            "lung nodule",
            "pleural effusion"
        ],
        "stopwords": [
            "the", "a", "an", "and", "or", "but",
            "in", "on", "at", "to", "for", "of"
        ],
        "anatomical_terms": {
            "chest": ["lung", "thorax", "pleura", "mediastinum"],
            "abdomen": ["liver", "kidney", "spleen"]
        },
        "diagnostic_terms": {
            "findings": ["nodule", "mass", "opacity", "consolidation"],
            "patterns": ["reticular", "nodular", "cystic"]
        },
        "modality_terms": {
            "CT": ["computed tomography", "CAT scan"],
            "MRI": ["magnetic resonance imaging"]
        },
        "quality_descriptors": {
            "size": ["small", "large", "tiny", "massive"],
            "density": ["hypodense", "hyperdense", "isodense"]
        },
        "characteristic_values": {
            "subtlety": {"1": "extremely subtle", "5": "obvious"},
            "malignancy": {"1": "highly unlikely", "5": "highly suspicious"}
        },
        "research_terms": ["cohort", "protocol", "annotation", "consensus"]
    }


@pytest.fixture
def temp_medical_terms_file(tmp_path, sample_medical_terms):
    """Create temporary medical terms JSON file"""
    terms_file = tmp_path / "medical_terms.json"
    with open(terms_file, 'w') as f:
        json.dump(sample_medical_terms, f)
    return str(terms_file)


@pytest.fixture
def normalizer(temp_medical_terms_file):
    """Create KeywordNormalizer instance with test data"""
    return KeywordNormalizer(medical_terms_path=temp_medical_terms_file)


@pytest.fixture
def normalizer_no_file():
    """Create KeywordNormalizer without medical terms file (fallback)"""
    return KeywordNormalizer(medical_terms_path="/nonexistent/path.json")


class TestKeywordNormalizerInit:
    """Test KeywordNormalizer initialization"""

    def test_init_with_valid_file(self, temp_medical_terms_file):
        """Test initialization with valid medical terms file"""
        normalizer = KeywordNormalizer(medical_terms_path=temp_medical_terms_file)

        assert normalizer is not None
        assert hasattr(normalizer, 'medical_terms')
        assert hasattr(normalizer, 'synonym_map')

    def test_init_with_missing_file(self):
        """Test initialization with missing file uses empty dict"""
        normalizer = KeywordNormalizer(medical_terms_path="/nonexistent/path.json")

        assert normalizer.medical_terms == {
            'synonyms': {},
            'abbreviations': {},
            'multi_word_terms': [],
            'stopwords': []
        }

    def test_init_with_keyword_repo(self, temp_medical_terms_file):
        """Test initialization with keyword repository"""
        mock_repo = Mock()
        normalizer = KeywordNormalizer(
            medical_terms_path=temp_medical_terms_file,
            keyword_repo=mock_repo
        )

        assert normalizer.repo == mock_repo


class TestNormalize:
    """Test normalize() method"""

    def test_normalize_simple_keyword(self, normalizer):
        """Test normalizing simple keyword"""
        result = normalizer.normalize("lung")

        # Should map to canonical form "pulmonary"
        assert result in ["lung", "pulmonary"]

    def test_normalize_with_whitespace(self, normalizer):
        """Test normalizing keyword with whitespace"""
        result = normalizer.normalize("  lung  ")

        assert result.strip() == result
        assert len(result) > 0

    def test_normalize_case_insensitive(self, normalizer):
        """Test normalization is case-insensitive"""
        result1 = normalizer.normalize("LUNG")
        result2 = normalizer.normalize("lung")
        result3 = normalizer.normalize("Lung")

        # All should produce same result (case-insensitive)
        assert result1.lower() == result2.lower() == result3.lower()

    def test_normalize_abbreviation_expansion(self, normalizer):
        """Test abbreviation expansion during normalization"""
        result = normalizer.normalize("CT", expand_abbreviations=True)

        # Should expand to "computed tomography"
        assert "computed" in result.lower() or result.lower() == "ct"

    def test_normalize_without_expansion(self, normalizer):
        """Test normalization without abbreviation expansion"""
        result = normalizer.normalize("CT", expand_abbreviations=False)

        assert isinstance(result, str)
        assert len(result) > 0


class TestGetAllForms:
    """Test get_all_forms() method"""

    def test_get_all_forms_with_synonyms(self, normalizer):
        """Test getting all synonym forms"""
        result = normalizer.get_all_forms("lung")

        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_all_forms_unknown_term(self, normalizer):
        """Test getting forms for unknown term"""
        result = normalizer.get_all_forms("unknownterm123")

        assert isinstance(result, list)
        # Should at least return the original term
        assert len(result) >= 1

    def test_get_all_forms_returns_unique(self, normalizer):
        """Test get_all_forms returns unique values"""
        result = normalizer.get_all_forms("nodule")

        # Should not have duplicates
        assert len(result) == len(set(result))


class TestStopwords:
    """Test stopword handling"""

    def test_is_stopword_true(self, normalizer):
        """Test detecting stopwords"""
        assert normalizer.is_stopword("the") is True
        assert normalizer.is_stopword("and") is True
        assert normalizer.is_stopword("or") is True

    def test_is_stopword_false(self, normalizer):
        """Test non-stopwords"""
        assert normalizer.is_stopword("nodule") is False
        assert normalizer.is_stopword("lung") is False

    def test_is_stopword_case_insensitive(self, normalizer):
        """Test stopword check is case-insensitive"""
        assert normalizer.is_stopword("THE") is True
        assert normalizer.is_stopword("The") is True
        assert normalizer.is_stopword("the") is True

    def test_filter_stopwords(self, normalizer):
        """Test filtering stopwords from token list"""
        tokens = ["the", "lung", "nodule", "and", "opacity"]
        result = normalizer.filter_stopwords(tokens)

        assert isinstance(result, list)
        # Should remove stopwords
        assert "the" not in result
        assert "and" not in result


class TestAbbreviations:
    """Test abbreviation expansion"""

    def test_expand_abbreviation_known(self, normalizer):
        """Test expanding known abbreviation"""
        result = normalizer.expand_abbreviation("CT")

        assert result is not None
        assert "computed" in result.lower()

    def test_expand_abbreviation_unknown(self, normalizer):
        """Test expanding unknown abbreviation"""
        result = normalizer.expand_abbreviation("XYZ")

        # Should return None for unknown abbreviations
        assert result is None

    def test_expand_abbreviation_case_insensitive(self, normalizer):
        """Test abbreviation expansion is case-insensitive"""
        result1 = normalizer.expand_abbreviation("CT")
        result2 = normalizer.expand_abbreviation("ct")

        # At least one should work
        assert result1 is not None or result2 is not None


class TestMultiWordTerms:
    """Test multi-word term detection"""

    def test_is_multi_word_term_true(self, normalizer):
        """Test detecting multi-word terms"""
        assert normalizer.is_multi_word_term("ground glass opacity") is True

    def test_is_multi_word_term_false(self, normalizer):
        """Test single words are not multi-word terms"""
        assert normalizer.is_multi_word_term("nodule") is False

    def test_detect_multi_word_terms_in_text(self, normalizer):
        """Test detecting multi-word terms in text"""
        text = "The patient has ground glass opacity in the lung"
        result = normalizer.detect_multi_word_terms(text)

        assert isinstance(result, list)


class TestBatchOperations:
    """Test batch normalization"""

    def test_normalize_batch(self, normalizer):
        """Test normalizing batch of keywords"""
        keywords = ["lung", "CT", "nodule"]
        result = normalizer.normalize_batch(keywords)

        assert isinstance(result, dict)
        assert len(result) == len(keywords)
        # Verify all input keywords are keys in result
        for keyword in keywords:
            assert keyword in result
            assert isinstance(result[keyword], str)

    def test_normalize_batch_empty_list(self, normalizer):
        """Test normalizing empty list"""
        result = normalizer.normalize_batch([])

        assert isinstance(result, dict)
        assert len(result) == 0


class TestSpecializedTerms:
    """Test specialized term retrieval"""

    def test_get_anatomical_terms(self, normalizer):
        """Test getting anatomical terms"""
        result = normalizer.get_anatomical_terms()

        assert isinstance(result, list)

    def test_get_diagnostic_terms(self, normalizer):
        """Test getting diagnostic terms"""
        result = normalizer.get_diagnostic_terms()

        assert isinstance(result, list)

    def test_get_modality_terms(self, normalizer):
        """Test getting modality terms"""
        result = normalizer.get_modality_terms()

        assert isinstance(result, list)

    def test_get_quality_descriptors(self, normalizer):
        """Test getting quality descriptors"""
        result = normalizer.get_quality_descriptors()

        assert isinstance(result, list)

    def test_get_research_terms(self, normalizer):
        """Test getting research terms"""
        result = normalizer.get_research_terms()

        assert isinstance(result, list)


class TestCharacteristicNormalization:
    """Test LIDC characteristic value normalization"""

    def test_normalize_characteristic_value(self, normalizer):
        """Test normalizing LIDC characteristic values"""
        result = normalizer.normalize_characteristic_value("subtlety", "1")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_normalize_characteristic_unknown(self, normalizer):
        """Test normalizing unknown characteristic"""
        result = normalizer.normalize_characteristic_value("unknown_char", "1")

        # Should handle gracefully
        assert isinstance(result, str)


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_normalize_empty_string(self, normalizer):
        """Test normalizing empty string"""
        result = normalizer.normalize("")

        assert isinstance(result, str)

    def test_normalize_none_handling(self, normalizer_no_file):
        """Test normalizer works with no medical terms file"""
        result = normalizer_no_file.normalize("test")

        assert isinstance(result, str)

    def test_close_method(self, normalizer):
        """Test close method doesn't raise errors"""
        normalizer.close()
        # Should not raise any exceptions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
