"""WordPress Publisher Service for auto-publishing to WordPress sites."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx

from app.models.article import Article
from app.models.published_post import PublishedPost
from app.services.event_publisher import event_publisher
from app.services.publishing_service import clean_html_for_wordpress

logger = logging.getLogger(__name__)


class Site:
    """Site configuration for WordPress publishing."""

    def __init__(
        self,
        id: UUID,
        wp_api_endpoint: str,
        wp_username: str,
        wp_app_password: str,
    ):
        self.id = id
        self.wp_api_endpoint = wp_api_endpoint.rstrip("/")
        self.wp_username = wp_username
        self.wp_app_password = wp_app_password


class WordPressPublisher:
    """Service for auto-publishing articles to WordPress via REST API."""

    def __init__(
        self,
        db=None,
        google_indexer=None,
        mock_mode: bool = False,
    ):
        """Initialize the WordPress Publisher.

        Args:
            db: Database session for saving published posts
            google_indexer: GoogleIndexer instance for pinging Google
            mock_mode: If True, simulate API calls without real HTTP requests
        """
        self.db = db
        self.google_indexer = google_indexer
        self._mock_mode = mock_mode
        self._mock_responses: List[Dict[str, Any]] = []

    @property
    def mock_mode(self) -> bool:
        """Check if publisher is in mock mode."""
        return self._mock_mode

    @property
    def mock_responses(self) -> List[Dict[str, Any]]:
        """Get list of mock responses (for testing)."""
        return self._mock_responses

    def clear_mock_responses(self) -> None:
        """Clear mock responses (for testing)."""
        self._mock_responses = []

    async def publish(
        self,
        article: Article,
        site: Site,
        categories: Optional[List[int]] = None,
        tags: Optional[List[int]] = None,
        featured_media: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Publish an article to WordPress.

        Args:
            article: The article to publish
            site: The WordPress site configuration
            categories: Optional list of category IDs
            tags: Optional list of tag IDs
            featured_media: Optional featured image ID

        Returns:
            Dict with wp_post_id, url, and other response data

        Raises:
            httpx.HTTPStatusError: If WordPress API returns an error
        """
        # Clean HTML content for WordPress
        clean_content = clean_html_for_wordpress(article.content or "")

        payload = {
            "title": article.title,
            "content": clean_content,
            "status": "publish",
        }

        if categories:
            payload["categories"] = categories
        if tags:
            payload["tags"] = tags
        if featured_media:
            payload["featured_media"] = featured_media

        if self._mock_mode:
            # Mock response for testing
            mock_response = {
                "id": 12345,
                "link": f"{site.wp_api_endpoint}/mock-post",
                "title": {"rendered": article.title},
                "status": "publish",
            }
            self._mock_responses.append({
                "article_id": str(article.id),
                "site_id": str(site.id),
                "payload": payload,
                "response": mock_response,
            })
            logger.info(f"Mock published article {article.id} to WordPress")

            wp_post_id = mock_response["id"]
            url = mock_response["link"]
        else:
            # Real API call
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{site.wp_api_endpoint}/wp-json/wp/v2/posts",
                    json=payload,
                    auth=(site.wp_username, site.wp_app_password),
                    timeout=30.0,
                )
                response.raise_for_status()

                data = response.json()
                wp_post_id = data["id"]
                url = data["link"]

                logger.info(f"Published article {article.id} to WordPress: {url}")

        # Save to database if session available
        if self.db:
            await self._save_published_post(
                article_id=article.id,
                site_id=site.id,
                wp_post_id=wp_post_id,
                url=url,
            )

        # Ping Google Indexing API
        if self.google_indexer:
            try:
                await self.google_indexer.request_indexing(url)
                logger.info(f"Pinged Google Indexing API for: {url}")
            except Exception as e:
                logger.warning(f"Failed to ping Google Indexing API: {e}")

        # Publish event
        await event_publisher.publish(
            "article.published",
            {
                "article_id": str(article.id),
                "url": url,
                "wp_post_id": wp_post_id,
                "site_id": str(site.id),
            },
        )

        return {
            "wp_post_id": wp_post_id,
            "url": url,
            "status": "published",
        }

    async def _save_published_post(
        self,
        article_id: UUID,
        site_id: UUID,
        wp_post_id: int,
        url: str,
    ) -> PublishedPost:
        """Save published post record to database."""
        published_post = PublishedPost(
            article_id=article_id,
            site_id=site_id,
            wp_post_id=wp_post_id,
            url=url,
            status="auto",
            published_at=datetime.now(timezone.utc),
        )
        self.db.add(published_post)
        await self.db.commit()
        await self.db.refresh(published_post)
        return published_post

    async def update_post(
        self,
        wp_post_id: int,
        site: Site,
        content: Optional[str] = None,
        title: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing WordPress post.

        Args:
            wp_post_id: The WordPress post ID
            site: The WordPress site configuration
            content: Optional new content
            title: Optional new title
            status: Optional new status

        Returns:
            Dict with updated post data
        """
        payload = {}
        if content is not None:
            payload["content"] = clean_html_for_wordpress(content)
        if title is not None:
            payload["title"] = title
        if status is not None:
            payload["status"] = status

        if not payload:
            return {"message": "No updates provided"}

        if self._mock_mode:
            mock_response = {
                "id": wp_post_id,
                "title": {"rendered": title or "Mock Title"},
                "status": status or "publish",
            }
            logger.info(f"Mock updated WordPress post {wp_post_id}")
            return mock_response

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{site.wp_api_endpoint}/wp-json/wp/v2/posts/{wp_post_id}",
                json=payload,
                auth=(site.wp_username, site.wp_app_password),
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def delete_post(
        self,
        wp_post_id: int,
        site: Site,
        force: bool = False,
    ) -> Dict[str, Any]:
        """Delete a WordPress post.

        Args:
            wp_post_id: The WordPress post ID
            site: The WordPress site configuration
            force: If True, permanently delete; otherwise move to trash

        Returns:
            Dict with deletion response
        """
        if self._mock_mode:
            logger.info(f"Mock deleted WordPress post {wp_post_id}")
            return {"deleted": True, "id": wp_post_id}

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{site.wp_api_endpoint}/wp-json/wp/v2/posts/{wp_post_id}",
                params={"force": force},
                auth=(site.wp_username, site.wp_app_password),
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_categories(self, site: Site) -> List[Dict[str, Any]]:
        """Get available categories from WordPress.

        Args:
            site: The WordPress site configuration

        Returns:
            List of category dictionaries
        """
        if self._mock_mode:
            return [
                {"id": 1, "name": "Uncategorized", "slug": "uncategorized"},
                {"id": 2, "name": "SEO", "slug": "seo"},
            ]

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{site.wp_api_endpoint}/wp-json/wp/v2/categories",
                auth=(site.wp_username, site.wp_app_password),
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_tags(self, site: Site) -> List[Dict[str, Any]]:
        """Get available tags from WordPress.

        Args:
            site: The WordPress site configuration

        Returns:
            List of tag dictionaries
        """
        if self._mock_mode:
            return [
                {"id": 1, "name": "seo", "slug": "seo"},
                {"id": 2, "name": "marketing", "slug": "marketing"},
            ]

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{site.wp_api_endpoint}/wp-json/wp/v2/tags",
                auth=(site.wp_username, site.wp_app_password),
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
