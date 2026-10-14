# Code and workflow audit — Campus Lost & Found

## Checks performed on the uploaded ZIP
- `app.py`, `db.py`, and HTML templates were read.
- Python syntax compilation passed for `app.py` before deployment edits; Jinja parsing passed for all 10 templates.
- Template `url_for` references were checked; the only names not in app route functions were Flask's built-in `static` endpoint.
- A live database-backed test could not be performed because the uploaded project did not include a schema or database dump. The isolated audit runtime also does not have Flask installed, so this is a static review, not proof that all pages run successfully against your database.

## Expected workflow from the code
1. `/` renders the home page.
2. `/register` inserts a row into `USER`, then a corresponding `STUDENT` row.
3. `/login` verifies the Werkzeug password hash and checks `ADMIN.user_id`; admins are redirected to `/admin`, students to `/dashboard`.
4. `/dashboard` loads profile, a student's own lost/found items and unread notification count.
5. `/report-lost` and `/report-found` insert items for the logged-in student.
6. `/items` lists open lost items and available found items.
7. `/find-matches/<id>` finds available found items with the same category and location, creates `MATCH` records with score 100, and displays matching found items.
8. `/claim/<id>` inserts a pending claim; `/claims` lists the logged-in student's claims.
9. `/admin` checks that the session user exists in `ADMIN`, then loads claims and matches.
10. Admin approval marks a claim Approved, marks the found item Claimed, and creates a notification. Rejection marks the claim Rejected and creates a notification.
11. `/notifications` lists the user's notifications and marks them read; `/logout` clears the session.

## Important findings before public launch

### High priority
- **Database credentials were hardcoded in `db.py` in the uploaded project.** Treat them as exposed: rotate/change that database password, remove it from source, and use environment variables. If the file was pushed to GitHub, deleting it from the latest commit does not remove it from Git history; rotate the password regardless.
- **The admin dashboard is protected by an ADMIN-table check**, but real access must be verified against the actual database. The admin user needs a matching `USER` row and `ADMIN.user_id` row. The password belongs in `USER.password` as a Werkzeug hash, not in `ADMIN`.
- **No schema file was present.** The included `schema.sql` is reconstructed from the SQL statements in `app.py`, not an original export. Compare it with your existing local database before using it.

### Security and correctness improvements recommended
- Admin approve/reject actions are implemented as GET routes, which can be triggered by a link. Change them to POST forms and add CSRF protection before treating the site as production-ready.
- `/logout` is a GET route; POST is preferable.
- The matching route does not verify that the lost item belongs to the logged-in student.
- Claim submission should verify that the target found item exists and is still `Available`, and should prevent a claim after it is already claimed. Current duplicate check only blocks another Pending claim from the same student for the same item.
- Multiple administrators could approve the same claim unless status is checked before update. Approval/rejection should be transactional and restricted to Pending claims.
- Registration and database failures can return raw exception text to the browser. Log details server-side and show a friendly error to users instead.
- User-controlled category/location IDs and form fields should be validated server-side; database foreign keys help, but friendly validation is needed.
- Add rate limiting / login attempt controls before a public production launch.

## Are all dashboards working?

**The source code has routes and templates for the student dashboard, item browsing, claims, notifications, and admin dashboard. Static checks passed for Python syntax and template parsing. However, I cannot honestly confirm that every dashboard and the complete end-to-end process works yet.** That requires the correct database schema, seeded categories/locations, a student account, an admin account, and a live test of every workflow step. Use the checklist in `DEPLOY_FREE.md` after connecting the database.

## Hosting files added
- `db.py` now reads `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, and `DB_SSL` from environment variables.
- `Procfile` and `render.yaml` use Gunicorn for Render.
- `schema.sql` defines the tables referenced by the current application and seeds basic categories/locations.
- `create_admin.py` creates an admin with a Werkzeug password hash.
- `DEPLOY_FREE.md` gives the step-by-step Render + TiDB Cloud setup.
