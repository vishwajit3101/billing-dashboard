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
| **infrastructure/main.tf** | ✓ | `infrastructure/main.tf` |
| **infrastructure/variables.tf** | ✓ | `infrastructure/variables.tf` |
| **infrastructure/outputs.tf** | ✓ | `infrastructure/outputs.tf` |

**Note:** The Python backend (config, schema, lambda_functions, tests) lives under `backend/`. Scripts at repo root (`scripts/`) are for deployment; `backend/scripts/` has DB init. Run tests from `backend/`: `python -m pytest tests/ -v`. Run local pipeline: `python tests/local_simulation.py` from `backend/`.
