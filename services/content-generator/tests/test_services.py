"""Tests for article service."""

from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.schemas.article import ArticleCreate, ArticleUpdate
from app.services.article_service import ArticleService


class TestArticleService:
    """Tests for ArticleService class."""

    @pytest_asyncio.fixture
    async def article_service(self, db_session: AsyncSession):
        """Get article service instance."""
        return ArticleService(db_session)

    @pytest_asyncio.fixture
    async def sample_article(self, article_service: ArticleService, test_workspace_id):
        """Create a sample article for testing."""
        data = ArticleCreate(
            workspace_id=test_workspace_id,
            title="Sample Article",
            content="Sample content",
            status="draft",
        )
        return await article_service.create(data)

    @pytest.mark.asyncio
    async def test_create_article(
        self, article_service: ArticleService, test_workspace_id
    ):
        """Test creating an article."""
        data = ArticleCreate(
            workspace_id=test_workspace_id,
            title="Test Article",
            content="Test content",
            status="draft",
        )
        article = await article_service.create(data)

        assert article.id is not None
        assert article.title == "Test Article"
        assert article.content == "Test content"
        assert article.status == "draft"
        assert article.workspace_id == test_workspace_id

    @pytest.mark.asyncio
    async def test_create_from_generation(
        self, article_service: ArticleService, test_workspace_id
    ):
        """Test creating an article from generation results."""
        plan_id = uuid4()
        article = await article_service.create_from_generation(
            workspace_id=test_workspace_id,
            plan_id=plan_id,
            title="Generated Article",
            content="Generated content",
            model="gpt-3.5-turbo",
            cost_usd=Decimal("0.05"),
            word_count=500,
            metadata={"tokens_used": {"prompt": 100, "completion": 400}},
        )

        assert article.id is not None
        assert article.title == "Generated Article"
        assert article.plan_id == plan_id
        assert article.cost_usd == Decimal("0.05")
        assert article.word_count == 500
        assert article.ai_model_used == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_get_by_id(
        self, article_service: ArticleService, sample_article: Article
    ):
        """Test getting an article by ID."""
        article = await article_service.get_by_id(sample_article.id)

        assert article is not None
        assert article.id == sample_article.id
        assert article.title == sample_article.title

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, article_service: ArticleService):
        """Test getting non-existent article returns None."""
        article = await article_service.get_by_id(uuid4())
        assert article is None

    @pytest.mark.asyncio
    async def test_get_by_workspace(
        self, article_service: ArticleService, test_workspace_id
    ):
        """Test getting articles by workspace."""
        # Create multiple articles
        for i in range(3):
            data = ArticleCreate(
                workspace_id=test_workspace_id,
                title=f"Article {i}",
            )
            await article_service.create(data)

        articles, total = await article_service.get_by_workspace(
            workspace_id=test_workspace_id
        )

        assert total == 3
        assert len(articles) == 3

    @pytest.mark.asyncio
    async def test_get_by_workspace_with_status_filter(
        self, article_service: ArticleService, test_workspace_id
    ):
        """Test filtering articles by status."""
        # Create articles with different statuses
        await article_service.create(
            ArticleCreate(
                workspace_id=test_workspace_id,
                title="Draft Article",
                status="draft",
            )
        )
        await article_service.create(
            ArticleCreate(
                workspace_id=test_workspace_id,
                title="Published Article",
                status="published",
            )
        )

        articles, total = await article_service.get_by_workspace(
            workspace_id=test_workspace_id,
            status="draft",
        )

        assert total == 1
        assert articles[0].status == "draft"

    @pytest.mark.asyncio
    async def test_get_by_workspace_pagination(
        self, article_service: ArticleService, test_workspace_id
    ):
        """Test pagination."""
        # Create multiple articles
        for i in range(5):
            await article_service.create(
                ArticleCreate(
                    workspace_id=test_workspace_id,
                    title=f"Article {i}",
                )
            )

        articles, total = await article_service.get_by_workspace(
            workspace_id=test_workspace_id,
            page=1,
            page_size=2,
        )

        assert total == 5
        assert len(articles) == 2

    @pytest.mark.asyncio
    async def test_update_article(
        self, article_service: ArticleService, sample_article: Article
    ):
        """Test updating an article."""
        data = ArticleUpdate(
            title="Updated Title",
            status="published",
        )
        updated = await article_service.update(sample_article.id, data)

        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.status == "published"

    @pytest.mark.asyncio
    async def test_update_article_not_found(self, article_service: ArticleService):
        """Test updating non-existent article returns None."""
        data = ArticleUpdate(title="New Title")
        updated = await article_service.update(uuid4(), data)
        assert updated is None

    @pytest.mark.asyncio
    async def test_delete_article(
        self, article_service: ArticleService, sample_article: Article
    ):
        """Test deleting an article."""
        deleted = await article_service.delete(sample_article.id)
        assert deleted is True

        # Verify it's deleted
        article = await article_service.get_by_id(sample_article.id)
        assert article is None

    @pytest.mark.asyncio
    async def test_delete_article_not_found(self, article_service: ArticleService):
        """Test deleting non-existent article returns False."""
        deleted = await article_service.delete(uuid4())
        assert deleted is False

    @pytest.mark.asyncio
    async def test_add_image(
        self, article_service: ArticleService, sample_article: Article
    ):
        """Test adding an image to an article."""
        image = await article_service.add_image(
            article_id=sample_article.id,
            filename="test-image.jpg",
            original_filename="my-photo.jpg",
            content_type="image/jpeg",
            size_bytes=1024,
            storage_path="articles/test/test-image.jpg",
        )

        assert image is not None
        assert image.filename == "test-image.jpg"
        assert image.original_filename == "my-photo.jpg"
        assert image.article_id == sample_article.id

    @pytest.mark.asyncio
    async def test_add_image_article_not_found(self, article_service: ArticleService):
        """Test adding image to non-existent article returns None."""
        image = await article_service.add_image(
            article_id=uuid4(),
            filename="test.jpg",
            original_filename="test.jpg",
            content_type="image/jpeg",
            size_bytes=1024,
            storage_path="test/test.jpg",
        )
        assert image is None

    @pytest.mark.asyncio
    async def test_get_images(
        self, article_service: ArticleService, sample_article: Article
    ):
        """Test getting images for an article."""
        # Add some images
        await article_service.add_image(
            article_id=sample_article.id,
            filename="image1.jpg",
            original_filename="photo1.jpg",
            content_type="image/jpeg",
            size_bytes=1024,
            storage_path="articles/test/image1.jpg",
        )
        await article_service.add_image(
            article_id=sample_article.id,
            filename="image2.png",
            original_filename="photo2.png",
            content_type="image/png",
            size_bytes=2048,
            storage_path="articles/test/image2.png",
        )

        images = await article_service.get_images(sample_article.id)
        assert len(images) == 2

    @pytest.mark.asyncio
    async def test_delete_image(
        self, article_service: ArticleService, sample_article: Article
    ):
        """Test deleting an image."""
        image = await article_service.add_image(
            article_id=sample_article.id,
            filename="to-delete.jpg",
            original_filename="delete-me.jpg",
            content_type="image/jpeg",
            size_bytes=1024,
            storage_path="articles/test/to-delete.jpg",
        )

        deleted = await article_service.delete_image(image.id)
        assert deleted is True

        images = await article_service.get_images(sample_article.id)
        assert len(images) == 0

    @pytest.mark.asyncio
    async def test_delete_image_not_found(self, article_service: ArticleService):
        """Test deleting non-existent image returns False."""
        deleted = await article_service.delete_image(uuid4())
        assert deleted is False
