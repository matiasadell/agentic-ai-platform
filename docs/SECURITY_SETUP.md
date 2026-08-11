# 🔐 Security Setup: Databricks Secrets Configuration

> Movido desde `SECURITY_SETUP.md` (raíz) el 2026-08-11.

## ⚠️ Estado real del repo vs. esta guía

Esta guía describe la práctica recomendada. **El repo hoy no la sigue completamente:**
- `8-multiagent.py` tiene una API key de Tavily hardcodeada en texto plano.
- `.env.example` tiene una API key real de Financial Modeling Prep (`FMP_API_KEY=...`), no un placeholder — un `.env.example` no debería tener ningún valor real.

Ambas deberían rotarse y removerse del código. Ver [PROJECT_STATUS.md](./PROJECT_STATUS.md) para el detalle. El resto de este documento describe cómo debería manejarse todo esto en producción.

## Overview

Todas las API keys sensibles se guardan en **Databricks Secrets**. Nunca hardcodear keys en notebooks o código.

## Configuración actual

### Secret Scope: `finsight`

| Secret Key | Purpose | Provider |
|------------|---------|----------|
| `fred-api-key` | Federal Reserve Economic Data | FRED API |
| `news-api-key` | Financial news search | NewsAPI |
| `alpha-vantage-api-key` | Datos financieros adicionales | Alpha Vantage |

## Quick Start

### 1. Verificar que existen

```bash
databricks secrets list-scopes
databricks secrets list-secrets --scope finsight
```

### 2. Leer secrets en código

**PySpark Notebooks:**
```python
from pyspark.dbutils import DBUtils
dbutils = DBUtils(spark)

fred_key = dbutils.secrets.get(scope="finsight", key="fred-api-key")
news_key = dbutils.secrets.get(scope="finsight", key="news-api-key")
alphavantage_key = dbutils.secrets.get(scope="finsight", key="alpha-vantage-api-key")

import os
os.environ['FRED_API_KEY'] = fred_key
os.environ['NEWS_API_KEY'] = news_key
os.environ['ALPHA_VANTAGE_API_KEY'] = alphavantage_key
```

**Databricks SDK:**
```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

fred_key = w.secrets.get_secret(scope="finsight", key="fred-api-key").value
```

## Agregar o actualizar secrets

**CLI:**
```bash
databricks secrets put-secret finsight fred-api-key
# o
echo "YOUR_API_KEY_HERE" | databricks secrets put-secret finsight fred-api-key
```

**SDK:**
```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
w.secrets.put_secret(scope="finsight", key="fred-api-key", string_value="YOUR_API_KEY_HERE")
```

## Buenas prácticas

### ✅ Hacer
- Usar siempre Databricks Secrets para keys y credenciales
- Pasar secrets a librerías vía variables de entorno
- Rotar keys regularmente (cada 90 días)
- Scopes separados para dev/staging/prod
- Auditar acceso a secrets

### ❌ No hacer
- Hardcodear API keys en notebooks o código
- Commitear secrets a Git
- Loguear secrets a consola o MLflow
- Compartir secrets por chat o email

## API Keys requeridas

| Key | Proveedor | Free tier | Rate limit | Usado por |
|---|---|---|---|---|
| FRED | fred.stlouisfed.org | Sí | 120 req/min | MacroDataWorker |
| NewsAPI | newsapi.org | 100 req/día | 100 req/día | MarketSentimentWorker / news workers |
| Alpha Vantage | alphavantage.co | 25 req/día | 25 req/día (free) | Fundamental agents |
| Financial Modeling Prep | site.financialmodelingprep.com | 250 req/día | 250 req/día (free) | Fundamental agents (ratios, earnings) |
| Tavily | tavily.com | 1000 req/mes | — | `8-multiagent.py`, búsqueda web |

## Troubleshooting

**Secret Not Found**
```bash
databricks secrets put-secret finsight fred-api-key
```

**Permission Denied**
```bash
databricks secrets put-acl finsight <user-email> READ
```

## Migrar keys hardcodeadas existentes

1. Guardar la key en Secrets:
   ```python
   w.secrets.put_secret(scope="finsight", key="fred-api-key", string_value="YOUR_KEY")
   ```
2. Reemplazar en el código:
   ```python
   # ❌ antes
   os.environ['FRED_API_KEY'] = 'hardcoded-value'
   # ✅ después
   os.environ['FRED_API_KEY'] = dbutils.secrets.get(scope="finsight", key="fred-api-key")
   ```
3. Borrar la key hardcodeada del código y del historial de Git si ya se commiteó.
4. Verificar que todo sigue funcionando.

## Auditar acceso

```python
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

secrets = w.secrets.list_secrets(scope="finsight")
for secret in secrets:
    print(f"Secret: {secret.key}, Last updated: {secret.last_updated_timestamp}")

acls = w.secrets.list_acls(scope="finsight")
for acl in acls:
    print(f"Principal: {acl.principal}, Permission: {acl.permission}")
```

## Scopes por ambiente

| Ambiente | Scope | Uso |
|---|---|---|
| Dev | `finsight-dev` | Testing |
| Staging | `finsight-staging` | Pre-producción |
| Prod | `finsight-prod` | Producción |

## Referencias

- [Databricks Secrets Documentation](https://docs.databricks.com/security/secrets/index.html)
- [Databricks Secret Scopes](https://docs.databricks.com/security/secrets/secret-scopes.html)
- [Databricks CLI Secrets Commands](https://docs.databricks.com/dev-tools/cli/secrets-cli.html)

---

**Fecha original:** 2026-07-24 · **Revisado:** 2026-08-11
