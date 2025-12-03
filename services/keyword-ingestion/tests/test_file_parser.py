"""Tests for file parser service."""

import pytest

from app.services.file_parser import FileParser


class TestFileParser:
    """Tests for FileParser class."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return FileParser()

    @pytest.mark.asyncio
    async def test_parse_csv_single_column(self, parser):
        """Test parsing CSV with single column."""
        content = b"keyword\napple\nbanana\ncherry\n"
        keywords = await parser.parse_csv(content)

        assert len(keywords) == 3
        assert "apple" in keywords
        assert "banana" in keywords
        assert "cherry" in keywords

    @pytest.mark.asyncio
    async def test_parse_csv_multiple_columns_takes_first(self, parser):
        """Test parsing CSV with multiple columns takes first column."""
        content = b"keyword,volume,difficulty\napple,1000,0.5\nbanana,2000,0.3\n"
        keywords = await parser.parse_csv(content)

        assert len(keywords) == 2
        assert "apple" in keywords
        assert "banana" in keywords

    @pytest.mark.asyncio
    async def test_parse_csv_empty_file(self, parser):
        """Test parsing empty CSV file."""
        content = b""
        keywords = await parser.parse_csv(content)

        assert keywords == []

    @pytest.mark.asyncio
    async def test_parse_csv_with_empty_values(self, parser):
        """Test parsing CSV with empty values."""
        content = b"keyword\napple\n\nbanana\n  \ncherry\n"
        keywords = await parser.parse_csv(content)

        # pandas reads empty lines as NaN, which get filtered out
        assert len(keywords) == 3
        assert "apple" in keywords
        assert "banana" in keywords
        assert "cherry" in keywords

    @pytest.mark.asyncio
    async def test_parse_txt_basic(self, parser):
        """Test parsing TXT file."""
        content = b"apple\nbanana\ncherry\n"
        keywords = await parser.parse_txt(content)

        assert len(keywords) == 3
        assert "apple" in keywords
        assert "banana" in keywords
        assert "cherry" in keywords

    @pytest.mark.asyncio
    async def test_parse_txt_with_empty_lines(self, parser):
        """Test parsing TXT file with empty lines."""
        content = b"apple\n\nbanana\n  \ncherry\n"
        keywords = await parser.parse_txt(content)

        assert len(keywords) == 3
        assert "apple" in keywords
        assert "banana" in keywords
        assert "cherry" in keywords

    @pytest.mark.asyncio
    async def test_parse_txt_empty_file(self, parser):
        """Test parsing empty TXT file."""
        content = b""
        keywords = await parser.parse_txt(content)

        assert keywords == []

    @pytest.mark.asyncio
    async def test_parse_txt_with_whitespace(self, parser):
        """Test parsing TXT file with leading/trailing whitespace."""
        content = b"  apple  \n  banana  \n  cherry  \n"
        keywords = await parser.parse_txt(content)

        assert len(keywords) == 3
        assert "apple" in keywords
        assert "banana" in keywords
        assert "cherry" in keywords

    @pytest.mark.asyncio
    async def test_parse_file_csv(self, parser):
        """Test parse_file with CSV."""
        content = b"keyword\napple\nbanana\n"
        keywords = await parser.parse_file(content, "test.csv")

        assert len(keywords) == 2

    @pytest.mark.asyncio
    async def test_parse_file_txt(self, parser):
        """Test parse_file with TXT."""
        content = b"apple\nbanana\n"
        keywords = await parser.parse_file(content, "test.txt")

        assert len(keywords) == 2

    @pytest.mark.asyncio
    async def test_parse_file_uppercase_extension(self, parser):
        """Test parse_file with uppercase extension."""
        content = b"apple\nbanana\n"
        keywords = await parser.parse_file(content, "test.TXT")

        assert len(keywords) == 2

    @pytest.mark.asyncio
    async def test_parse_file_invalid_extension(self, parser):
        """Test parse_file with invalid extension raises error."""
        content = b"apple\nbanana\n"

        with pytest.raises(ValueError) as excinfo:
            await parser.parse_file(content, "test.xlsx")

        assert "Unsupported file format" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_parse_txt_latin1_encoding(self, parser):
        """Test parsing TXT file with latin-1 encoding."""
        # Create content with latin-1 specific character
        content = "café\nnaïve\n".encode("latin-1")
        keywords = await parser.parse_txt(content)

        assert len(keywords) == 2
