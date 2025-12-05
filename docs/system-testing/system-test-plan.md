# Auto-SEO System Test Plan

## Overview

This document outlines the comprehensive test plan for the Auto-SEO platform, covering all implemented phases and ensuring integration between modules.

**Test Scope:** Complete system verification based on:
- Master specification: `docs/phase-specs/master-spec.txt`
- Individual phase specifications: `docs/phase-specs/phases/*.phase.yml`

**Testing Strategy:** Validate that the system behaves according to acceptance criteria defined in all phase specifications, with particular emphasis on:
- Service health and connectivity
- API endpoint functionality
- Event-driven workflows
- Cross-module integration
- End-to-end user journeys

---

## Test Strategy

### In Scope

1. **Unit Tests** - Per-service business logic validation
2. **API Tests** - REST endpoint validation for each service
3. **Integration Tests** - Cross-service communication and event flows
4. **End-to-End Tests** - Complete user journeys through the system

### Out of Scope

- Performance/load testing under production-level traffic
- Security penetration testing
- External third-party API integration (LLM, WordPress, Google APIs) - mocked
- Production environment deployment verification
- UI visual regression testing

### Test Environment

- All tests run against mocked external services (LLMs, RabbitMQ, MinIO, databases)
- Use pytest for Python services
- Use Playwright/Jest for frontend E2E tests
- Tests should be deterministic and CI-ready

---

## End-to-End Flows Mapping

### Flow 1: Keyword Import to Content Plan

**Description:** User uploads keywords → keywords are processed → topic clusters are created → content plan is generated

**Related Phases:**
- PHASE-003: Keyword Ingestion MVP
- PHASE-005: SEO Strategy MVP

**Events:**
- `keyword.list.imported`
- `cluster.created`
- `content.plan.created`

### Flow 2: Content Generation Pipeline

**Description:** Content plan is created → article is generated → SEO score is calculated → article is approved/regenerated

**Related Phases:**
- PHASE-005: SEO Strategy MVP
- PHASE-007: Content Generation MVP
- PHASE-009: SEO Scoring MVP

**Events:**
- `content.plan.created`
- `article.generated`
- `article.scored`
- `article.approved_for_publishing` / `article.generate.request`

### Flow 3: Publishing Flow

**Description:** Approved article → exported for publishing → published post is tracked

**Related Phases:**
- PHASE-009: SEO Scoring MVP
- PHASE-011: Publishing MVP

**Events:**
- `article.approved_for_publishing`
- `article.published`

### Flow 4: Analytics & Feedback

**Description:** Published article → performance data recorded → summary reports generated

**Related Phases:**
- PHASE-011: Publishing MVP
- PHASE-013: Feedback & Analytics MVP

**Data Flow:**
- PostgreSQL → ClickHouse
- Performance metrics tracking

---

## Test Suites

### Suite 1: Core Services API Tests

**Related Phases:** PHASE-001, PHASE-002

| Test Case | Description | Phase ID | Expected Result |
|-----------|-------------|----------|-----------------|
| AUTH-001 | User registration endpoint | PHASE-002 | User created with valid JWT |
| AUTH-002 | User login returns JWT | PHASE-002 | Valid JWT token returned |
| AUTH-003 | Invalid login returns 401 | PHASE-002 | 401 Unauthorized |
| AUTH-004 | Protected route requires auth | PHASE-002 | 401 without token |
| WS-001 | Create workspace | PHASE-002 | Workspace created successfully |
| WS-002 | List user workspaces | PHASE-002 | Returns workspace list |
| WS-003 | Workspace isolation | PHASE-002 | Users see only their workspaces |
| SITE-001 | Add site to workspace | PHASE-002 | Site created with encrypted credentials |
| SITE-002 | List sites | PHASE-002 | Returns sites for workspace |
| HEALTH-001 | Service health endpoints | PHASE-001 | All services return healthy |

### Suite 2: Keyword Ingestion Service Tests

**Related Phases:** PHASE-003

| Test Case | Description | Phase ID | Expected Result |
|-----------|-------------|----------|-----------------|
| KW-001 | Upload CSV file | PHASE-003 | Keywords imported successfully |
| KW-002 | Upload TXT file | PHASE-003 | Keywords imported successfully |
| KW-003 | Keyword normalization | PHASE-003 | Keywords lowercased and trimmed |
| KW-004 | Duplicate removal | PHASE-003 | Duplicates removed within list |
| KW-005 | List keyword lists | PHASE-003 | Returns paginated list |
| KW-006 | Get keyword list stats | PHASE-003 | Returns count and status breakdown |
| KW-007 | Event published on import | PHASE-003 | `keyword.list.imported` event |
| KW-008 | Invalid file format error | PHASE-003 | 400 Bad Request |
| KW-009 | File size limit | PHASE-003 | 413 for files > 10MB |

### Suite 3: SEO Strategy Service Tests

**Related Phases:** PHASE-005

| Test Case | Description | Phase ID | Expected Result |
|-----------|-------------|----------|-----------------|
| CLUSTER-001 | Create topic cluster | PHASE-005 | Cluster created |
| CLUSTER-002 | Add keywords to cluster | PHASE-005 | Keywords assigned |
| CLUSTER-003 | Remove keyword from cluster | PHASE-005 | Keyword unassigned |
| PLAN-001 | Create content plan | PHASE-005 | Plan created with priority |
| PLAN-002 | List content plans | PHASE-005 | Returns filtered list |
| PLAN-003 | Update content plan | PHASE-005 | Plan updated |
| PLAN-004 | Event on plan creation | PHASE-005 | `content.plan.created` event |

### Suite 4: Content Generation Service Tests

**Related Phases:** PHASE-007

| Test Case | Description | Phase ID | Expected Result |
|-----------|-------------|----------|-----------------|
| ART-001 | Generate article from plan | PHASE-007 | Article created with content |
| ART-002 | Article cost tracking | PHASE-007 | Cost recorded accurately |
| ART-003 | Article word count | PHASE-007 | Word count calculated |
| ART-004 | Upload article image | PHASE-007 | Image stored in S3/MinIO |
| ART-005 | List articles | PHASE-007 | Returns workspace articles |
| ART-006 | Event on generation | PHASE-007 | `article.generated` event |

### Suite 5: SEO Scoring Service Tests

**Related Phases:** PHASE-009

| Test Case | Description | Phase ID | Expected Result |
|-----------|-------------|----------|-----------------|
| SCORE-001 | Create SEO score | PHASE-009 | Score saved with checklist |
| SCORE-002 | Score calculation | PHASE-009 | Score = checked/total * 100 |
| SCORE-003 | Update score checklist | PHASE-009 | Checklist updated |
| SCORE-004 | Get article score | PHASE-009 | Returns score with breakdown |

### Suite 6: Publishing Service Tests

**Related Phases:** PHASE-011

| Test Case | Description | Phase ID | Expected Result |
|-----------|-------------|----------|-----------------|
| PUB-001 | Export article as HTML | PHASE-011 | Returns clean HTML |
| PUB-002 | Export article as Markdown | PHASE-011 | Returns Markdown |
| PUB-003 | Record published post | PHASE-011 | Published post tracked |
| PUB-004 | List published posts | PHASE-011 | Returns posts for site |

### Suite 7: Analytics Service Tests

**Related Phases:** PHASE-013

| Test Case | Description | Phase ID | Expected Result |
|-----------|-------------|----------|-----------------|
| ANALYTICS-001 | Record performance data | PHASE-013 | Data stored in ClickHouse |
| ANALYTICS-002 | Get summary report | PHASE-013 | Returns aggregated metrics |
| ANALYTICS-003 | Get article performance | PHASE-013 | Returns time series data |

### Suite 8: Event Flow Integration Tests

**Related Phases:** All phases

| Test Case | Description | Related Phases | Expected Result |
|-----------|-------------|----------------|-----------------|
| EVT-001 | Keyword import triggers event | PHASE-003 | Event published to bus |
| EVT-002 | Cluster creation triggers event | PHASE-005 | Event published to bus |
| EVT-003 | Content plan triggers event | PHASE-005 | Event published to bus |
| EVT-004 | Article generation triggers event | PHASE-007 | Event published to bus |
| EVT-005 | Article approval triggers event | PHASE-009 | Event published to bus |
| EVT-006 | Article publishing triggers event | PHASE-011 | Event published to bus |
| EVT-007 | Complete flow from keyword to publish | ALL | All events in sequence |

### Suite 9: Cross-Module Integration Tests

| Test Case | Description | Related Phases | Expected Result |
|-----------|-------------|----------------|-----------------|
| INT-001 | Keywords available for clustering | PHASE-003, PHASE-005 | Keywords from Module 1 accessible in Module 2 |
| INT-002 | Content plans reference clusters | PHASE-005, PHASE-007 | Plans link to valid clusters |
| INT-003 | Articles reference content plans | PHASE-007, PHASE-009 | Articles link to valid plans |
| INT-004 | Published posts reference articles | PHASE-009, PHASE-011 | Posts link to valid articles |
| INT-005 | Analytics track published articles | PHASE-011, PHASE-013 | Analytics reference valid posts |

### Suite 10: End-to-End User Journey Tests

**Related Phases:** PHASE-015, PHASE-016

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| E2E-001 | Login page displays correctly | Login form visible |
| E2E-002 | Registration page accessible | Registration form visible |
| E2E-003 | Protected routes redirect to login | Redirect works |
| E2E-004 | Dashboard accessible after login | Dashboard loads |
| E2E-005 | Keyword page structure | Page loads |
| E2E-006 | Content plans page structure | Page loads |
| E2E-007 | Clustering page structure | Page loads |
| E2E-008 | Analytics page structure | Page loads |

---

## Negative Tests & Error Handling

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| ERR-001 | Invalid JWT token | 401 Unauthorized |
| ERR-002 | Expired JWT token | 401 Unauthorized |
| ERR-003 | Missing required fields | 422 Validation Error |
| ERR-004 | Resource not found | 404 Not Found |
| ERR-005 | Duplicate resource | 409 Conflict |
| ERR-006 | Unauthorized workspace access | 403 Forbidden |
| ERR-007 | Invalid file format upload | 400 Bad Request |
| ERR-008 | Rate limiting exceeded | 429 Too Many Requests |

---

## Test Execution Plan

### Phase 1: Unit Tests
- Run existing unit tests in each service
- Verify core business logic

### Phase 2: API Tests
- Test all REST endpoints with mocked dependencies
- Verify request/response schemas

### Phase 3: Integration Tests
- Test event publishing and consumption
- Verify cross-service data flows

### Phase 4: E2E Tests
- Run Playwright tests against frontend
- Verify complete user workflows

---

## Test Coverage Goals

| Component | Target Coverage |
|-----------|----------------|
| Auth Service | ≥ 80% |
| Keyword Ingestion | ≥ 80% |
| SEO Strategy | ≥ 75% |
| Content Generator | ≥ 80% |
| SEO Scorer | ≥ 75% |
| Publishing | ≥ 75% |
| Analytics | ≥ 75% |
| Integration Tests | All major flows |
| E2E Tests | All major pages |

---

## Test Run Status

*See `docs/system-testing/runs/` for detailed test run logs.*

### Current Status: ✅ COMPLETE - ALL TESTS PASSING

**Last Run:** 2025-12-05  
**Total Tests:** 501  
**Passed:** 501  
**Failed:** 0  

| Suite | Status | Pass | Fail | Skip |
|-------|--------|------|------|------|
| Integration Tests | ✅ Passed | 20 | 0 | 0 |
| Auth Service | ✅ Passed | 32 | 0 | 0 |
| Keyword Ingestion | ✅ Passed | 110 | 0 | 0 |
| SEO Strategy | ✅ Passed | 95 | 0 | 0 |
| Content Generator | ✅ Passed | 171 | 0 | 0 |
| SEO Scorer | ✅ Passed | 62 | 0 | 0 |
| Frontend (Vitest) | ✅ Passed | 11 | 0 | 0 |

---

## Known Issues & Bugs

**No critical issues found.** All tests are passing.

### Resolved Issues

1. **Auth Service SQLite Compatibility (Fixed)**
   - Models now use database-aware type selection for SQLite testing
   - Schema qualification conditionally applied

2. **Test Expectations Corrected (Fixed)**
   - Updated HTTP status code assertions from 403 to 401 for missing authentication

### Minor Warnings (Non-blocking)

1. Pydantic V2 deprecation warnings for class-based config
2. Python crypt module deprecation (passlib dependency)

---

## Appendix: Phase Dependencies

```
PHASE-001 (Infrastructure)
    └── PHASE-002 (Core Services)
        ├── PHASE-003 (Keyword Ingestion MVP)
        │   ├── PHASE-004 (Keyword Automation)
        │   └── PHASE-005 (SEO Strategy MVP)
        │       ├── PHASE-006 (SEO Strategy Automation)
        │       └── PHASE-007 (Content Generation MVP)
        │           ├── PHASE-008 (Content Generation Automation)
        │           └── PHASE-009 (SEO Scoring MVP)
        │               ├── PHASE-010 (SEO Scoring Automation)
        │               └── PHASE-011 (Publishing MVP)
        │                   └── PHASE-012 (Publishing Automation)
        │                       └── PHASE-013 (Feedback & Analytics MVP)
        │                           └── PHASE-014 (Strategic Learning)
        └── PHASE-015 (Dashboard UI) [Depends on all module APIs]
            └── PHASE-016 (E2E Integration Testing)
```

---

*Last Updated: 2025-12-05*
