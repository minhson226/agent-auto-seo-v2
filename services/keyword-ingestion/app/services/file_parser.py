"""File parser service for CSV and TXT files."""

import io
import logging
from typing import List

import pandas as pd

logger = logging.getLogger(__name__)


class FileParser:
    """Parser for CSV and TXT files containing keywords."""

    async def parse_csv(self, content: bytes) -> List[str]:
        """Parse CSV file and extract keywords.

        Expected format:
        - Single column: keyword
        - Or multiple columns, take first column
        - Skip header if detected

        Args:
            content: File content as bytes

        Returns:
            List of keywords extracted from the file
        """
        try:
            # Try to read CSV with pandas
            df = pd.read_csv(io.BytesIO(content))

            if df.empty:
                return []

            # Get first column (assuming keywords are in first column)
            first_column = df.iloc[:, 0]

            # Filter out empty values and convert to strings
            keywords = [
                str(val).strip()
                for val in first_column.dropna().tolist()
                if str(val).strip()
            ]

            logger.info(f"Parsed {len(keywords)} keywords from CSV")
            return keywords

        except pd.errors.EmptyDataError:
            logger.warning("Empty CSV file")
            return []
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            raise ValueError(f"Failed to parse CSV file: {str(e)}")

    async def parse_txt(self, content: bytes) -> List[str]:
        """Parse TXT file, one keyword per line.

        Args:
            content: File content as bytes

        Returns:
            List of keywords extracted from the file
        """
        try:
            # Decode bytes to string
            text = content.decode("utf-8")

            # Split by newlines and filter empty lines
            keywords = [
                line.strip()
                for line in text.split("\n")
                if line.strip()
            ]

            logger.info(f"Parsed {len(keywords)} keywords from TXT")
            return keywords

        except UnicodeDecodeError:
            # Try with different encodings
            try:
                text = content.decode("latin-1")
                keywords = [
                    line.strip()
                    for line in text.split("\n")
                    if line.strip()
                ]
                logger.info(f"Parsed {len(keywords)} keywords from TXT (latin-1 encoding)")
                return keywords
            except Exception as e:
                logger.error(f"Error decoding TXT file: {e}")
                raise ValueError(f"Failed to decode TXT file: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing TXT: {e}")
            raise ValueError(f"Failed to parse TXT file: {str(e)}")

    async def parse_file(self, content: bytes, filename: str) -> List[str]:
        """Parse file based on its extension.

        Args:
            content: File content as bytes
            filename: Original filename to determine format

        Returns:
            List of keywords extracted from the file

        Raises:
            ValueError: If file format is not supported
        """
        filename_lower = filename.lower()

        if filename_lower.endswith(".csv"):
            return await self.parse_csv(content)
        elif filename_lower.endswith(".txt"):
            return await self.parse_txt(content)
        else:
            raise ValueError(
                f"Unsupported file format. Expected .csv or .txt, got: {filename}"
            )
