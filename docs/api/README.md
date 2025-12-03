# Auto-SEO API Documentation

## Overview

The Auto-SEO Platform provides a RESTful API for managing users, workspaces, sites, and API keys. All API endpoints are accessible through the API Gateway.

## Base URL

- Development: `http://localhost:8080/api/v1`
- Production: `https://api.autoseo.com/api/v1`

## Authentication

All protected endpoints require a JWT Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## Rate Limiting

- **Per User**: 100 requests per minute
- **Per Workspace**: 1000 requests per minute
- **Anonymous**: 50 requests per minute

When rate limited, the API returns `429 Too Many Requests` with a `Retry-After` header.

## API Endpoints

### Authentication

#### Register User

```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "is_verified": false,
  "is_superuser": false,
  "created_at": "2025-11-23T14:00:00Z",
  "updated_at": "2025-11-23T14:00:00Z",
  "full_name": "John Doe"
}
```

#### Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Refresh Token

```http
POST /auth/refresh-token
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Get Current User

```http
GET /auth/me
Authorization: Bearer <access_token>
```

### Workspaces

#### List Workspaces

```http
GET /workspaces
Authorization: Bearer <access_token>
```

Query Parameters:
- `skip` (int): Number of items to skip (default: 0)
- `limit` (int): Maximum items to return (default: 100)

#### Create Workspace

```http
POST /workspaces
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "My Workspace",
  "slug": "my-workspace",
  "description": "A workspace for my SEO projects"
}
```

#### Get Workspace

```http
GET /workspaces/{workspace_id}
Authorization: Bearer <access_token>
```

#### Update Workspace

```http
PUT /workspaces/{workspace_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Updated Workspace Name",
  "description": "Updated description"
}
```

#### Delete Workspace

```http
DELETE /workspaces/{workspace_id}
Authorization: Bearer <access_token>
```

#### List Workspace Members

```http
GET /workspaces/{workspace_id}/members
Authorization: Bearer <access_token>
```

#### Add Workspace Member

```http
POST /workspaces/{workspace_id}/members
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "role": "member"
}
```

Role options: `admin`, `member`, `viewer`

#### Remove Workspace Member

```http
DELETE /workspaces/{workspace_id}/members/{user_id}
Authorization: Bearer <access_token>
```

### Sites

#### List Sites

```http
GET /workspaces/{workspace_id}/sites
Authorization: Bearer <access_token>
```

#### Create Site

```http
POST /workspaces/{workspace_id}/sites
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "My Blog",
  "domain": "myblog.com",
  "platform": "wordpress",
  "wp_api_endpoint": "https://myblog.com/wp-json",
  "wp_auth_type": "application_password",
  "wp_credentials": {
    "username": "admin",
    "password": "app_password_here"
  }
}
```

Platform options: `wordpress`, `ghost`, `custom`

#### Get Site

```http
GET /sites/{site_id}
Authorization: Bearer <access_token>
```

#### Update Site

```http
PUT /sites/{site_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Updated Blog Name",
  "is_active": true
}
```

#### Delete Site

```http
DELETE /sites/{site_id}
Authorization: Bearer <access_token>
```

### API Keys

#### List API Keys

```http
GET /workspaces/{workspace_id}/api-keys
Authorization: Bearer <access_token>
```

#### Create API Key

```http
POST /workspaces/{workspace_id}/api-keys
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "service_name": "openai",
  "api_key": "sk-..."
}
```

Service name examples: `openai`, `google`, `ahrefs`, `semrush`

**Note**: The API key value is encrypted before storage and is never returned in responses.

#### Get API Key

```http
GET /api-keys/{api_key_id}
Authorization: Bearer <access_token>
```

**Note**: This only returns metadata, not the actual key value.

#### Delete API Key

```http
DELETE /api-keys/{api_key_id}
Authorization: Bearer <access_token>
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful deletion) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing or invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |

## Swagger UI

Interactive API documentation is available at:

- Auth Service: `http://localhost:8081/api/docs`
- Notification Service: `http://localhost:8082/api/docs`

## Health Endpoints

Each service exposes health endpoints:

- `GET /health` - Liveness probe
- `GET /ready` - Readiness probe
- `GET /metrics` - Prometheus metrics
