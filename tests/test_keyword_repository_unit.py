"""
Comprehensive Unit Tests for KeywordRepository

Tests repository methods with mocked database dependencies.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session
from datetime import datetime

from src.maps.database.keyword_repository import KeywordRepository
from src.maps.database.keyword_models import (
    Keyword,
    KeywordSource,
    KeywordStatistics,
    KeywordSynonym,
    KeywordSearchHistory
)


@pytest.fixture
def mock_session():
    """Create mock database session"""
    mock = MagicMock(spec=Session)
    return mock


@pytest.fixture
def mock_db_config():
    """Mock database configuration"""
    with patch('src.maps.database.keyword_repository.get_db_config') as mock:
        mock_config = Mock()
        mock_config.get_engine.return_value = Mock()
        mock.return_value = mock_config
        yield mock


@pytest.fixture
def repository(mock_db_config):
    """Create KeywordRepository with mocked database"""
    with patch('src.maps.database.keyword_repository.sessionmaker') as mock_sessionmaker:
        mock_session_class = Mock()
        mock_sessionmaker.return_value = mock_session_class
        repo = KeywordRepository()
        return repo


class TestKeywordRepositoryInit:
    """Test KeywordRepository initialization"""

    def test_init_with_default_database(self, mock_db_config):
        """Test initialization with default database name"""
        with patch('src.maps.database.keyword_repository.sessionmaker'):
            repo = KeywordRepository()
            assert repo is not None

    def test_init_with_custom_database(self, mock_db_config):
        """Test initialization with custom database name"""
        with patch('src.maps.database.keyword_repository.sessionmaker'):
            repo = KeywordRepository(database="custom_db")
            assert repo is not None


class TestAddKeyword:
    """Test add_keyword() method"""

    def test_add_keyword_basic(self, repository, mock_session):
        """Test adding keyword with basic fields"""
        repository._get_session = Mock(return_value=mock_session)
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        mock_keyword = Keyword(
            keyword_id=1,
            keyword_text="nodule",
            category="finding",
            normalized_form="nodule",
            created_at=datetime.now()
        )
        
        def mock_add(obj):
            obj.keyword_id = 1
            obj.created_at = datetime.now()
            return obj
        
        mock_session.add = mock_add
        mock_session.commit = Mock()
        
        result = repository.add_keyword("nodule", category="finding")
        
        assert result is not None
        mock_session.commit.assert_called_once()

    def test_add_keyword_duplicate_returns_existing(self, repository, mock_session):
        """Test adding duplicate keyword returns existing"""
        repository._get_session = Mock(return_value=mock_session)
        
        existing_keyword = Keyword(
            keyword_id=1,
            keyword_text="nodule",
            category="finding",
            normalized_form="nodule",
            created_at=datetime.now()
        )
        
        mock_session.query.return_value.filter_by.return_value.first.return_value = existing_keyword
        
        result = repository.add_keyword("nodule", category="finding")
        
        assert result == existing_keyword
        mock_session.commit.assert_not_called()

    def test_add_keyword_with_all_fields(self, repository, mock_session):
        """Test adding keyword with all optional fields"""
        repository._get_session = Mock(return_value=mock_session)
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        mock_keyword = Keyword(
            keyword_id=1,
            keyword_text="pulmonary nodule",
            category="anatomy",
            normalized_form="pulmonary_nodule",
            created_at=datetime.now()
        )
        
        def mock_add(obj):
            obj.keyword_id = 1
            obj.created_at = datetime.now()
            return obj
        
        mock_session.add = mock_add
        mock_session.commit = Mock()
        
        result = repository.add_keyword(
            "pulmonary nodule",
            category="anatomy",
            normalized_form="pulmonary_nodule"
        )
        
        assert result is not None
        mock_session.commit.assert_called_once()


class TestGetKeyword:
    """Test get_keyword() method"""

    def test_get_keyword_exists(self, repository, mock_session):
        """Test getting keyword that exists"""
        repository._get_session = Mock(return_value=mock_session)
        
        mock_keyword = Keyword(
            keyword_id=1,
            keyword_text="nodule",
            category="finding",
            created_at=datetime.now()
        )
        
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_keyword
        
        result = repository.get_keyword(1)
        
        assert result == mock_keyword
        assert result.keyword_id == 1

    def test_get_keyword_not_found(self, repository, mock_session):
        """Test getting keyword that doesn't exist"""
        repository._get_session = Mock(return_value=mock_session)
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        result = repository.get_keyword(999)
        
        assert result is None


class TestGetKeywordByText:
    """Test get_keyword_by_text() method"""

    def test_get_keyword_by_text_exists(self, repository, mock_session):
        """Test getting keyword by text"""
        repository._get_session = Mock(return_value=mock_session)
        
        mock_keyword = Keyword(
            keyword_id=1,
            keyword_text="nodule",
            category="finding",
            created_at=datetime.now()
        )
        
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_keyword
        
        result = repository.get_keyword_by_text("nodule")
        
        assert result == mock_keyword
        assert result.keyword_text == "nodule"

    def test_get_keyword_by_text_not_found(self, repository, mock_session):
        """Test getting keyword by text that doesn't exist"""
        repository._get_session = Mock(return_value=mock_session)
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        result = repository.get_keyword_by_text("unknown_keyword")
        
        assert result is None


class TestSearchKeywords:
    """Test search_keywords() method"""

    def test_search_keywords_basic(self, repository, mock_session):
        """Test basic keyword search"""
        repository._get_session = Mock(return_value=mock_session)
        
        mock_keywords = [
            Keyword(keyword_id=1, keyword_text="nodule", category="finding"),
            Keyword(keyword_id=2, keyword_text="pulmonary nodule", category="anatomy")
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value.limit.return_value.all.return_value = mock_keywords
        mock_session.query.return_value = mock_query
        
        result = repository.search_keywords("nodule", limit=10)
        
        assert isinstance(result, list)
        assert len(result) == 2

    def test_search_keywords_with_category_filter(self, repository, mock_session):
        """Test keyword search with category filter"""
        repository._get_session = Mock(return_value=mock_session)
        
        mock_keywords = [
            Keyword(keyword_id=1, keyword_text="nodule", category="finding")
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.limit.return_value.all.return_value = mock_keywords
        mock_session.query.return_value = mock_query
        
        result = repository.search_keywords("nodule", category="finding", limit=10)
        
        assert len(result) == 1
        assert result[0].category == "finding"

    def test_search_keywords_empty_results(self, repository, mock_session):
        """Test keyword search with no results"""
        repository._get_session = Mock(return_value=mock_session)
        
        mock_query = Mock()
        mock_query.filter.return_value.limit.return_value.all.return_value = []
        mock_session.query.return_value = mock_query
        
        result = repository.search_keywords("unknown_term", limit=10)
        
        assert isinstance(result, list)
        assert len(result) == 0


class TestGetAllKeywords:
    """Test get_all_keywords() method"""

    def test_get_all_keywords_no_limit(self, repository, mock_session):
        """Test getting all keywords without limit"""
        repository._get_session = Mock(return_value=mock_session)
        
        mock_keywords = [
            Keyword(keyword_id=i, keyword_text=f"keyword{i}", category="test")
            for i in range(5)
        ]
        
        mock_query = Mock()
        mock_query.all.return_value = mock_keywords
        mock_session.query.return_value = mock_query
        
        result = repository.get_all_keywords()
        
        assert len(result) == 5

    def test_get_all_keywords_with_limit(self, repository, mock_session):
        """Test getting all keywords with limit"""
        repository._get_session = Mock(return_value=mock_session)
        
        mock_keywords = [
            Keyword(keyword_id=i, keyword_text=f"keyword{i}", category="test")
            for i in range(3)
        ]
        
        mock_query = Mock()
        mock_query.limit.return_value.all.return_value = mock_keywords
        mock_session.query.return_value = mock_query
        
        result = repository.get_all_keywords(limit=3)
        
        assert len(result) == 3


class TestAddKeywordSource:
    """Test add_keyword_source() method"""

    def test_add_keyword_source_new(self, repository, mock_session):
        """Test adding new keyword source"""
        repository._get_session = Mock(return_value=mock_session)
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        mock_source = KeywordSource(
            source_id=1,
            keyword_id=1,
            source_type="xml",
            source_file="test.xml",
            frequency=1,
            sector="lidc"
        )
        
        def mock_add(obj):
            obj.source_id = 1
            return obj
        
        mock_session.add = mock_add
        mock_session.commit = Mock()
        
        result = repository.add_keyword_source(
            keyword_id=1,
            source_type="xml",
            source_file="test.xml",
            sector="lidc"
        )
        
        assert result is not None
        mock_session.commit.assert_called_once()

    def test_add_keyword_source_duplicate_increments_frequency(self, repository, mock_session):
        """Test adding duplicate source increments frequency"""
        repository._get_session = Mock(return_value=mock_session)
        
        existing_source = KeywordSource(
            source_id=1,
            keyword_id=1,
            source_type="xml",
            source_file="test.xml",
            frequency=1,
            sector="lidc"
        )
        
        mock_session.query.return_value.filter_by.return_value.first.return_value = existing_source
        mock_session.commit = Mock()
        
        result = repository.add_keyword_source(
            keyword_id=1,
            source_type="xml",
            source_file="test.xml",
            sector="lidc"
        )
        
        assert result == existing_source
        assert result.frequency == 2
        mock_session.commit.assert_called_once()


class TestGetSourcesForKeyword:
    """Test get_sources_for_keyword() method"""

    def test_get_sources_for_keyword(self, repository, mock_session):
        """Test getting sources for keyword"""
        repository._get_session = Mock(return_value=mock_session)
        
        mock_sources = [
            KeywordSource(source_id=1, keyword_id=1, source_file="test1.xml"),
            KeywordSource(source_id=2, keyword_id=1, source_file="test2.xml")
        ]
        
        mock_query = Mock()
        mock_query.filter_by.return_value.all.return_value = mock_sources
        mock_session.query.return_value = mock_query
        
        result = repository.get_sources_for_keyword(1)
        
        assert len(result) == 2

    def test_get_sources_for_keyword_with_sector_filter(self, repository, mock_session):
        """Test getting sources with sector filter"""
        repository._get_session = Mock(return_value=mock_session)
        
        mock_sources = [
            KeywordSource(source_id=1, keyword_id=1, source_file="test1.xml", sector="lidc")
        ]
        
        mock_query = Mock()
        mock_query.filter_by.return_value.filter_by.return_value.all.return_value = mock_sources
        mock_session.query.return_value = mock_query
        
        result = repository.get_sources_for_keyword(1, sector="lidc")
        
        assert len(result) == 1


class TestSynonymOperations:
    """Test synonym-related methods"""

    def test_add_synonym(self, repository, mock_session):
        """Test adding synonym"""
        repository._get_session = Mock(return_value=mock_session)
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        mock_synonym = KeywordSynonym(
            synonym_id=1,
            synonym_text="lung nodule",
            canonical_keyword_id=1,
            synonym_type="alternate"
        )
        
        def mock_add(obj):
            obj.synonym_id = 1
            return obj
        
        mock_session.add = mock_add
        mock_session.commit = Mock()
        
        result = repository.add_synonym(
            "lung nodule",
            canonical_keyword_id=1,
            synonym_type="alternate"
        )
        
        assert result is not None
        mock_session.commit.assert_called_once()

    def test_get_canonical_keyword(self, repository, mock_session):
        """Test getting canonical keyword from synonym"""
        repository._get_session = Mock(return_value=mock_session)
        
        mock_keyword = Keyword(keyword_id=1, keyword_text="nodule")
        mock_synonym = KeywordSynonym(
            synonym_id=1,
            synonym_text="lung nodule",
            canonical_keyword_id=1,
            canonical_keyword=mock_keyword
        )
        
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_synonym
        
        result = repository.get_canonical_keyword("lung nodule")
        
        assert result == mock_keyword

    def test_get_synonyms_for_keyword(self, repository, mock_session):
        """Test getting all synonyms for keyword"""
        repository._get_session = Mock(return_value=mock_session)
        
        mock_synonyms = [
            KeywordSynonym(synonym_id=1, synonym_text="lung nodule", canonical_keyword_id=1),
            KeywordSynonym(synonym_id=2, synonym_text="pulmonary mass", canonical_keyword_id=1)
        ]
        
        mock_query = Mock()
        mock_query.filter_by.return_value.all.return_value = mock_synonyms
        mock_session.query.return_value = mock_query
        
        result = repository.get_synonyms_for_keyword(1)
        
        assert len(result) == 2


class TestSearchAnalytics:
    """Test search analytics methods"""

    def test_record_search(self, repository, mock_session):
        """Test recording search query"""
        repository._get_session = Mock(return_value=mock_session)
        
        mock_session.add = Mock()
        mock_session.commit = Mock()
        
        repository.record_search(
            "nodule",
            result_count=5,
            execution_time_ms=12.5,
            user_sector="lidc"
        )
        
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_get_search_analytics(self, repository, mock_session):
        """Test getting search analytics"""
        repository._get_session = Mock(return_value=mock_session)
        
        mock_searches = [
            {
                'query_text': 'nodule',
                'result_count': 5,
                'execution_time_ms': 12.5,
                'search_timestamp': datetime.now()
            }
        ]
        
        mock_query = Mock()
        mock_query.order_by.return_value.limit.return_value.all.return_value = [
            KeywordSearchHistory(
                query_text='nodule',
                result_count=5,
                execution_time_ms=12.5,
                search_timestamp=datetime.now()
            )
        ]
        mock_session.query.return_value = mock_query
        
        result = repository.get_search_analytics(limit=10)
        
        assert isinstance(result, list)


class TestContextManager:
    """Test context manager methods"""

    def test_context_manager_enter_exit(self, mock_db_config):
        """Test repository as context manager"""
        with patch('src.maps.database.keyword_repository.sessionmaker'):
            with KeywordRepository() as repo:
                assert repo is not None

    def test_close_method(self, repository):
        """Test close method"""
        repository.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
