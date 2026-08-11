import sys

# Don't write .pyc files to __pycache__/ for any module imported after this
# package. Set here (rather than via the PYTHONDONTWRITEBYTECODE env var)
# because this code runs across local dev, Databricks notebooks, and
# Databricks jobs/clusters - environments where env vars aren't
# consistently configured (and env-var-based config here is being phased
# out in favor of Databricks Secrets, which isn't the right place for an
# interpreter flag like this anyway).
#
# Caveat: this module's own __init__.pyc still gets written once - the
# write decision for a module is made before its code runs, so it can't
# retroactively opt itself out. Everything imported afterward (src.agents,
# src.schemas, etc.) is correctly skipped.
sys.dont_write_bytecode = True
