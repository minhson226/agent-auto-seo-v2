"""
Locust load testing for Auto-SEO API.
Run with: locust -f tests/performance/locustfile.py --users 100 --spawn-rate 10
"""

from locust import HttpUser, task, between, events
import json
import random
from uuid import uuid4


class AutoSEOUser(HttpUser):
    """Simulated Auto-SEO platform user for load testing."""
    
    wait_time = between(1, 3)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None
        self.workspace_id = None
    
    def on_start(self):
        """Login when user starts."""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": f"loadtest_{random.randint(1, 1000)}@example.com",
                "password": "loadtestpassword123",
            },
            catch_response=True,
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token", data.get("access_token"))
            if self.token:
                self.client.headers["Authorization"] = f"Bearer {self.token}"
                response.success()
            else:
                response.failure("No token in response")
        elif response.status_code in [401, 403]:
            # Expected failure for non-existent test users - don't count as error
            # Tests will continue with unauthenticated endpoints
            response.success()
        else:
            # Actual server errors should be tracked
            response.failure(f"Login failed with status {response.status_code}")
    
    @task(10)
    def health_check(self):
        """Check API health endpoint."""
        self.client.get("/health")
    
    @task(5)
    def get_keyword_lists(self):
        """Get keyword lists for workspace."""
        if self.workspace_id:
            self.client.get(f"/api/v1/keyword-lists?workspace_id={self.workspace_id}")
        else:
            self.client.get("/api/v1/keyword-lists")
    
    @task(5)
    def get_content_plans(self):
        """Get content plans."""
        if self.workspace_id:
            self.client.get(f"/api/v1/content-plans?workspace_id={self.workspace_id}")
        else:
            self.client.get("/api/v1/content-plans")
    
    @task(3)
    def get_articles(self):
        """Get articles list."""
        self.client.get("/api/v1/articles")
    
    @task(2)
    def get_seo_scores(self):
        """Get SEO scores."""
        self.client.get("/api/v1/scores")
    
    @task(1)
    def get_analytics_summary(self):
        """Get analytics summary."""
        self.client.get("/api/v1/analytics/summary")
    
    @task(1)
    def get_workspaces(self):
        """Get user workspaces."""
        response = self.client.get("/api/v1/workspaces")
        if response.status_code == 200:
            try:
                data = response.json()
                if data and len(data) > 0:
                    self.workspace_id = data[0].get("id")
            except (json.JSONDecodeError, IndexError, KeyError):
                pass


class ContentCreationUser(HttpUser):
    """User that focuses on content creation workflow."""
    
    wait_time = between(2, 5)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None
    
    def on_start(self):
        """Login when user starts."""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "contentuser@example.com",
                "password": "contentpassword123",
            },
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token", data.get("access_token"))
            if self.token:
                self.client.headers["Authorization"] = f"Bearer {self.token}"
    
    @task(3)
    def view_content_plans(self):
        """View content plans."""
        self.client.get("/api/v1/content-plans")
    
    @task(2)
    def view_clusters(self):
        """View topic clusters."""
        self.client.get("/api/v1/clusters")
    
    @task(1)
    def generate_article_request(self):
        """Simulate article generation request."""
        self.client.post(
            "/api/v1/articles/generate",
            json={
                "plan_id": str(uuid4()),
                "title": "Load Test Article",
                "target_keywords": ["test", "performance"],
            },
        )


class AnalyticsUser(HttpUser):
    """User that focuses on viewing analytics."""
    
    wait_time = between(1, 2)
    
    @task(5)
    def dashboard_metrics(self):
        """Get dashboard metrics."""
        self.client.get("/api/v1/analytics/dashboard")
    
    @task(3)
    def content_performance(self):
        """Get content performance data."""
        self.client.get("/api/v1/analytics/content-performance")
    
    @task(2)
    def keyword_rankings(self):
        """Get keyword ranking data."""
        self.client.get("/api/v1/analytics/rankings")
    
    @task(1)
    def export_report(self):
        """Request analytics export."""
        self.client.get("/api/v1/analytics/export?format=json")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log when load test starts."""
    print("Starting Auto-SEO Load Test")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log when load test ends."""
    print("Auto-SEO Load Test Complete")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Failure rate: {environment.stats.total.fail_ratio * 100:.2f}%")
