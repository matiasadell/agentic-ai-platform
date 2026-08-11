# 🔐 Security Setup: Databricks Secrets Configuration

## Overview

All sensitive API keys for the Agentic AI Platform are stored in **Databricks Secrets** for security best practices. Never hardcode API keys in notebooks or code!

## Current Configuration

### Secret Scope: `finsight`

All API keys are stored in the `finsight` scope:

| Secret Key | Purpose | Provider |
|------------|---------|----------|
| `fred-api-key` | Federal Reserve Economic Data | FRED API |
| `news-api-key` | Financial news search | NewsAPI |
| `alpha-vantage-api-key` | Additional financial data | Alpha Vantage |

## Quick Start

### 1. Verify Secrets Exist

```bash
databricks secrets list-scopes
databricks secrets list-secrets --scope finsight
```

### 2. Access Secrets in Code

**Python (PySpark Notebooks):**

```python
from pyspark.dbutils import DBUtils
dbutils = DBUtils(spark)

# Read secrets
fred_key = dbutils.secrets.get(scope="finsight", key="fred-api-key")
news_key = dbutils.secrets.get(scope="finsight", key="news-api-key")
alphavantage_key = dbutils.secrets.get(scope="finsight", key="alpha-vantage-api-key")

# Set as environment variables
import os
os.environ['FRED_API_KEY'] = fred_key
os.environ['NEWS_API_KEY'] = news_key
os.environ['ALPHA_VANTAGE_API_KEY'] = alphavantage_key
```

**Python (Databricks SDK):**

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Read secrets
fred_key = w.secrets.get_secret(scope="finsight", key="fred-api-key").value
news_key = w.secrets.get_secret(scope="finsight", key="news-api-key").value
alphavantage_key = w.secrets.get_secret(scope="finsight", key="alpha-vantage-api-key").value
```

## Adding or Updating Secrets

### Using Databricks CLI

```bash
# Add a new secret (interactive - will prompt for value)
databricks secrets put-secret finsight fred-api-key

# Or pipe the value
echo "YOUR_API_KEY_HERE" | databricks secrets put-secret finsight fred-api-key
```

### Using Databricks SDK (Python)

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Add or update a secret
w.secrets.put_secret(
    scope="finsight",
    key="fred-api-key",
    string_value="YOUR_API_KEY_HERE"
)
```

### Using Databricks UI

1. Go to **Settings** > **Developer** > **Access Tokens**
2. Navigate to **Secrets** tab
3. Select scope `finsight`
4. Add or update secrets

## Security Best Practices

### ✅ DO:
- **Always use Databricks Secrets** for API keys and credentials
- **Use environment variables** to pass secrets to libraries
- **Rotate API keys regularly** (every 90 days)
- **Use separate scopes** for dev/staging/prod environments
- **Audit secret access** regularly
- **Document required secrets** in README files

### ❌ DON'T:
- **Never hardcode API keys** in notebooks or code files
- **Never commit secrets** to Git repositories
- **Never log secrets** to console or MLflow
- **Never share secrets** via chat or email
- **Never print or display** secret values

## Required API Keys

### 1. FRED API Key
- **Provider**: Federal Reserve Economic Data (FRED)
- **Sign up**: https://fred.stlouisfed.org/docs/api/api_key.html
- **Free tier**: Yes (no credit card required)
- **Rate limits**: 120 requests/minute
- **Used by**: MacroDataWorker (GDP, inflation, unemployment)

### 2. NewsAPI Key
- **Provider**: NewsAPI.org
- **Sign up**: https://newsapi.org/register
- **Free tier**: 100 requests/day
- **Paid tier**: $449/month for production use
- **Rate limits**: 100 requests/day (free), unlimited (paid)
- **Used by**: MarketSentimentWorker (news search, sentiment)

### 3. Alpha Vantage API Key
- **Provider**: Alpha Vantage
- **Sign up**: https://www.alphavantage.co/support/#api-key
- **Free tier**: 25 requests/day
- **Paid tier**: From $49.99/month
- **Rate limits**: 25 requests/day (free), 75 requests/minute (paid)
- **Used by**: Future workers (stock prices, technical indicators)

## Troubleshooting

### Secret Not Found Error

```python
# Error: Secret does not exist with scope: finsight and key: fred-api-key
```

**Solution**: Add the secret using the CLI or SDK:

```bash
databricks secrets put-secret finsight fred-api-key
```

### Permission Denied Error

```python
# Error: User does not have READ permission on scope: finsight
```

**Solution**: Request access from workspace admin:

```bash
databricks secrets put-acl finsight <user-email> READ
```

### Empty Secret Value

```python
# Secret exists but returns empty string
```

**Solution**: Re-add the secret with a value:

```bash
echo "YOUR_API_KEY" | databricks secrets put-secret finsight fred-api-key
```

## Migrating Existing Hardcoded Keys

If you have notebooks with hardcoded API keys:

1. **Store keys in secrets** (once):
   ```python
   from databricks.sdk import WorkspaceClient
   w = WorkspaceClient()
   
   w.secrets.put_secret(scope="finsight", key="fred-api-key", string_value="YOUR_KEY")
   w.secrets.put_secret(scope="finsight", key="news-api-key", string_value="YOUR_KEY")
   ```

2. **Update notebook code** (replace hardcoded keys):
   ```python
   # ❌ OLD (insecure)
   os.environ['FRED_API_KEY'] = 'b1c128442d6248c6c1e3dd6b6c1c87ad'
   
   # ✅ NEW (secure)
   os.environ['FRED_API_KEY'] = dbutils.secrets.get(scope="finsight", key="fred-api-key")
   ```

3. **Remove hardcoded keys** from code
4. **Verify** the notebook still works
5. **Delete old versions** that contain hardcoded keys

## Auditing Secret Access

Track who accessed which secrets:

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

# List all secrets in scope
secrets = w.secrets.list_secrets(scope="finsight")
for secret in secrets:
    print(f"Secret: {secret.key}, Last updated: {secret.last_updated_timestamp}")

# View ACLs (access control lists)
acls = w.secrets.list_acls(scope="finsight")
for acl in acls:
    print(f"Principal: {acl.principal}, Permission: {acl.permission}")
```

## Environment-Specific Scopes

For production deployments, use separate scopes:

| Environment | Scope Name | Purpose |
|-------------|------------|---------|
| Development | `finsight-dev` | Testing, experimentation |
| Staging | `finsight-staging` | Pre-production validation |
| Production | `finsight-prod` | Live production workloads |

## Additional Resources

- [Databricks Secrets Documentation](https://docs.databricks.com/security/secrets/index.html)
- [Databricks Secret Scopes](https://docs.databricks.com/security/secrets/secret-scopes.html)
- [Secret Management Best Practices](https://docs.databricks.com/security/secrets/best-practices.html)
- [Databricks CLI Secrets Commands](https://docs.databricks.com/dev-tools/cli/secrets-cli.html)

---

**Last Updated**: 2026-07-24  
**Maintained By**: FinSight AI Platform Team
