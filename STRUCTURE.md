# Billing Watch — Project structure checklist

Use this to verify all expected files exist. Paths are relative to the repo root.

| Expected path | Exists | Actual path |
|---------------|--------|-------------|
| **.env.example** | ✓ | `backend/.env.example` |
| **config.py** | ✓ | `backend/config.py` |
| **requirements.txt** | ✓ | `backend/requirements.txt` |
| **README.md** | ✓ | `backend/README.md` (also `README.md` at root) |
| **schema/init_db.sql** | ✓ | `backend/schema/init_db.sql` |
| **scripts/init_database.py** | ✓ | `backend/scripts/init_database.py` |
| **scripts/deploy.sh** | ✓ | `scripts/deploy.sh` |
| **scripts/package_lambdas.sh** | ✓ | `scripts/package_lambdas.sh` |
| **lambda_functions/billing_fetcher/** | ✓ | `backend/lambda_functions/billing_fetcher/` |
| **lambda_functions/posthog_processor/** | ✓ | `backend/lambda_functions/posthog_processor/` |
| **lambda_functions/risk_calculator/** | ✓ | `backend/lambda_functions/risk_calculator/` |
| **lambda_functions/alert_engine/** | ✓ | `backend/lambda_functions/alert_engine/` |
| **lambda_functions/dashboard_api/** | ✓ | `backend/lambda_functions/dashboard_api/` |
| **tests/test_billing_fetcher.py** | ✓ | `backend/tests/test_billing_fetcher.py` |
| **tests/test_posthog_processor.py** | ✓ | `backend/tests/test_posthog_processor.py` |
| **tests/test_risk_calculator.py** | ✓ | `backend/tests/test_risk_calculator.py` |
| **tests/test_alert_engine.py** | ✓ | `backend/tests/test_alert_engine.py` |
| **tests/test_api.py** | ✓ | `backend/tests/test_api.py` |
| **tests/local_simulation.py** | ✓ | `backend/tests/local_simulation.py` |
| **infrastructure/main.tf** | ✓ | `infrastructure/main.tf` |
| **infrastructure/variables.tf** | ✓ | `infrastructure/variables.tf` |
| **infrastructure/outputs.tf** | ✓ | `infrastructure/outputs.tf` |

**Note:** The Python backend (config, schema, lambda_functions, tests) lives under `backend/`. Scripts at repo root (`scripts/`) are for deployment; `backend/scripts/` has DB init. Run tests from `backend/`: `python -m pytest tests/ -v`. Run local pipeline: `python tests/local_simulation.py` from `backend/`.
