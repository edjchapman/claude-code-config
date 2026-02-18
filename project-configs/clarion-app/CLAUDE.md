@frontend/.rulesync/rules/overview.md
@frontend/.rulesync/rules/frontend.md

# Clarion App - Claude Code Project Memory

## Running Backend Tests

To run backend Django tests, use docker compose with Django's test runner from the project root:

```bash
# Run all tests for a specific app
cd ~/Development/BuiltAI/clarion_app
docker compose run --rm api bash -c "cd /app/clarion-api && uv run manage.py test comparison_tools"

# Run specific test module
docker compose run --rm api bash -c "cd /app/clarion-api && uv run manage.py test comparison_tools.tests.test_commands"

# Run specific test class
docker compose run --rm api bash -c "cd /app/clarion-api && uv run manage.py test comparison_tools.tests.test_commands.CompareCashflowsCommandTest"

# Run specific test method
docker compose run --rm api bash -c "cd /app/clarion-api && uv run manage.py test comparison_tools.tests.test_commands.CompareCashflowsCommandTest.test_writes_report_when_mismatches_found"

# Run tests in parallel (as CI does)
docker compose run --rm api bash -c "cd /app/clarion-api && uv run manage.py test comparison_tools --parallel=4"

# Run with verbose output
docker compose run --rm api bash -c "cd /app/clarion-api && uv run manage.py test comparison_tools --verbosity=2"

# Stop on first failure
docker compose run --rm api bash -c "cd /app/clarion-api && uv run manage.py test comparison_tools --failfast"

# Run multiple apps at once
docker compose run --rm api bash -c "cd /app/clarion-api && uv run manage.py test cashflow cashflow_forecast portfolios"
```

**Note**: Tests use Django's standard test runner with `manage.py test`. Use Python dotted path notation (e.g., `app.tests.module.TestClass.test_method`).

### Test Configuration

- **Settings module**: Tests use Django test settings which override storage to use local filesystem instead of S3
- **Parallel execution**: Use `--parallel=4` flag for 4 parallel workers
- **Container rebuild**: If you modify `backend/pyproject.toml`, rebuild the container with `docker compose build api`

## Python Version & Type Hints

This project targets **Python 3.12**. Do NOT add `from __future__ import annotations` to files - it's unnecessary since Python 3.10+ natively supports:

- Union syntax: `int | None` instead of `Optional[int]` or `Union[int, None]`
- Built-in generics: `list[str]` instead of `List[str]`

## Codebase Architecture

### Backend Structure (`backend/clarion-api/`)

| Component | Location | Notes |
|-----------|----------|-------|
| Django Apps | `backend/clarion-api/` | Each app is a top-level directory |
| Models | `app/models/` | e.g., `project/models/tenancy.py` |
| Serializers | `app/serializers/` | DRF serializers |
| Views | `app/views/` | ViewSets and API views |
| Django Migrations | `app/migrations/` | Standard Django migrations |
| Data Migrations | `migration_script.py` | `MigrationScript` class for data transforms |

### Frontend Structure (`frontend/src/`)

| Component | Location | Notes |
|-----------|----------|-------|
| Pages | `pages/` | Route-based organization |
| Components | `components/` | Shared components |
| Types | `types/` | TypeScript interfaces |
| Forms | `*Form.tsx` | react-hook-form pattern |

### Key Systems

#### Cashflow V2 (Hamilton)

- **Location:** `backend/clarion-api/cashflow_v2/`
- **Features:** `cashflow_v2/forecast/features/` - calculation modules
- **Tenant Events:** `cashflow_v2/forecast/features/tenant/events/`
- **Tests:** `cashflow_v2/tests/`

#### Tenancy/Lease System

- **Model:** `project/models/tenancy.py` - `TenancyBase` class
- **Forms:** `frontend/src/pages/Projects/ProjectPages/NewTenantPages/UnitLeaseDetails/Forms/`
- **Next Lease Fields:** `reversion_*` prefix (e.g., `reversion_lease_length`)

#### OpEx System

- **Model:** `project/opex/models/opex_cost.py`
- **Frontend:** `frontend/src/pages/Projects/ProjectPages/ProjectAssumptions/Tabs/OperatingExpense/`

#### Portfolios

- **Model:** `portfolios/models/portfolio.py`
- **Pages:** `frontend/src/pages/Portfolios/`

#### Metrics

- **Registry:** `project/metrics/enums.py` - `MetricRegistry` enum (source of truth)
- **Fixtures:** `project/fixtures_data/metric_definitions.json`

### Common Patterns

#### Adding a New Field

1. Add to Django model with migration
2. Add to serializer
3. Add to frontend TypeScript interface (`types/`)
4. Add to relevant form component
5. Update tests

#### Data Migrations

Follow pattern in `migration_script.py`:

```python
def migrate_example(self):
    Model.objects.filter(old_field__isnull=False).update(
        new_field=F('old_field'),
        new_mechanism='NEW_VALUE'
    )
```

#### Service Charge Fields

- **Income:** `service_charge_income`, `service_charge_income_mechanism`
- **Cost:** `service_charges_pct`, `service_charges_cal_mechanism`
- **Mechanisms:** `PERCENTAGE_OF_ERV`, `PRICE_PER_AREA`

## Jira API Access

Environment variables for Jira access are configured in `~/.zshrc`:

- `JIRA_USERNAME` - Atlassian account email
- `JIRA_API_TOKEN` - API token from <https://id.atlassian.com/manage-profile/security/api-tokens>

### Fetching Tickets

```bash
# Fetch a single ticket
curl -s -u "${JIRA_USERNAME}:${JIRA_API_TOKEN}" \
  -H "Content-Type: application/json" \
  "https://builtai.atlassian.net/rest/api/3/issue/BIL-XXXX?expand=renderedFields"

# Search with JQL
curl -s -u "${JIRA_USERNAME}:${JIRA_API_TOKEN}" \
  -H "Content-Type: application/json" \
  "https://builtai.atlassian.net/rest/api/3/search?jql=status='Ready%20to%20Refine'"
```

### Refinement Process

Use `/refinement BIL-XXXX` to generate technical analysis for backlog refinement:

1. Fetches ticket details from Jira API
2. Explores codebase for relevant files
3. Generates documentation in `./refinement/` directory:
   - `README.md` - Summary table and action items
   - `BIL-XXXX_title.md` - Individual ticket analysis

**Output includes:** Story point estimates, key files, implementation steps, clarifying questions, and risk assessment.
