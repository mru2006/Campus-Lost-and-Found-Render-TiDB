# Campus Lost & Found — free hosting setup (Render + TiDB Cloud)

This project is a Flask app that currently uses MySQL Connector/Python. The simplest free-tier option that keeps the MySQL-style database is a Render free web service plus a TiDB Cloud Starter MySQL-compatible database. Free tiers can change; check provider quotas before relying on it for a long-term/production service. Render free web services sleep after inactivity and may take about a minute to wake up. TiDB credentials must be kept private.

## What is included
- `db.py`: reads database credentials from environment variables instead of hardcoding a local root password.
- `schema.sql`: schema matching the SQL queries in `app.py`, plus starter categories/locations.
- `create_admin.py`: safely creates/updates an admin user and hashes the password.
- `Procfile` and `render.yaml`: deployment configuration.
- `.env.example`: names of the required environment variables.

## 1. Create the cloud database
1. Create a TiDB Cloud Starter cluster at https://tidbcloud.com/ (choose the free Starter option).
2. Create database `lost_found_db` (or another name you will use in `DB_NAME`).
3. Open the cluster's connection details and copy the host, port, username, password, and database name. Use the exact values shown in the provider's connection instructions; the port may differ from the example in `render.yaml`.
4. Connect with a MySQL-compatible client and run the full `schema.sql` file against the new empty database. Do not run it blindly on an existing database.

## 2. Push this project to GitHub
1. Extract this project folder and replace the old `db.py`, `requirements.txt`, and add the included deployment files to the repository root (the folder containing `app.py`).
2. Ensure `venv/`, `.env`, and real credentials are not committed. Remove the virtual environment from Git if it was tracked previously.
3. Commit and push the changes to GitHub.

## 3. Create the Render web service
1. Sign in at https://render.com/ and choose **New → Blueprint** (or create a **Web Service** manually).
2. Select your GitHub repository. If using Blueprint, Render reads `render.yaml`.
3. Set these environment variables in Render's service settings using the TiDB connection details:
   - `FLASK_SECRET_KEY`: generate a long random secret (Render can generate it automatically).
   - `DB_HOST`: TiDB host
   - `DB_PORT`: TiDB port from its connection instructions
   - `DB_USER`: TiDB username
   - `DB_PASSWORD`: TiDB password
   - `DB_NAME`: database name, e.g. `lost_found_db`
   - `DB_SSL`: `true`
4. Deploy. Check **Logs** if deployment fails. `gunicorn app:app` is the start command.

## 4. Create the admin account
Run this once against the cloud database, using the same DB_* values. One straightforward way is on your computer:

PowerShell example (from the project folder, with venv activated):

```powershell
$env:DB_HOST = "YOUR_TIDB_HOST"
$env:DB_PORT = "YOUR_TIDB_PORT"
$env:DB_USER = "YOUR_TIDB_USER"
$env:DB_PASSWORD = "YOUR_TIDB_PASSWORD"
$env:DB_NAME = "lost_found_db"
$env:DB_SSL = "true"
python create_admin.py
```

Enter the admin name, email and a unique password when prompted. Do not put a real password in source code or GitHub. This script can update the password if the email already exists and ensures the user is in the `ADMIN` table.

## 5. End-to-end workflow to test after deployment
1. Open the Render URL. The home page should load.
2. Register a test student using a unique email and PRN.
3. Log in as the student. It should open `/dashboard`.
4. Report a lost item and verify it appears on the dashboard.
5. Report a found item with the same category and location.
6. Open Browse Items and test Find Matches from a lost item. Current matching is rule-based: category and location must match; the app records a score of 100. This is not an AI/ML model.
7. Submit a claim for a found item.
8. Log out and sign in with the admin email. It should open `/admin`.
9. Verify the pending claim and match appear in the admin dashboard. Approve or reject a test claim.
10. Log back in as the student and check My Claims and Notifications. Approval should mark the found item `Claimed`; approval/rejection should create a notification.
11. Verify a non-admin student cannot open `/admin`.

## Important limitations found in the source audit
- The ZIP did not contain an original `schema.sql` or database dump, so `schema.sql` here was reconstructed from the SQL statements in `app.py`. Compare it with your existing local database before using it; if your actual schema differs, adjust it first.
- The source can be syntax-checked, and the templates parse, but the actual dashboards and full workflow cannot be certified without connecting to a database populated with the schema and exercising each route.
- The source's admin approve/reject routes use GET requests and have no CSRF protection. For a public production system, these actions should be changed to POST forms with CSRF protection before launch.
- The claim route currently blocks duplicate *pending* claims only; it should also prevent claims on items already marked `Claimed` and should validate item status server-side.
- The lost-item matching route accepts any logged-in user and does not verify that the lost item belongs to that user. Consider adding ownership checks.
- Registration and reporting errors can return raw exception text to users. Replace these with logged server-side errors and friendly messages before production.
- `app.py` requires `FLASK_SECRET_KEY`; set it in the hosting dashboard. Never commit the actual secret.
- Render free web services sleep after 15 minutes idle and use an ephemeral filesystem. This app's relational data is stored in TiDB, not on Render's local filesystem.
