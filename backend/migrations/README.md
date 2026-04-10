Schema is created automatically on API startup via SQLAlchemy `create_all`.

For production, generate Alembic revisions from `app.models` and replace auto-create with migrations.
