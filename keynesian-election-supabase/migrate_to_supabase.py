"""
Migrate data from the local SQLite database.db into the database pointed to
by the DATABASE_URL environment variable (your Supabase Postgres connection
string).

HOW TO USE
----------
1. Create your Supabase project and copy its connection string
   (Project Settings -> Database -> Connection string -> URI).
2. Set it as an environment variable before running this script:

       Windows (cmd):
           set DATABASE_URL=postgresql://postgres:YOURPASSWORD@YOURHOST:5432/postgres
           python migrate_to_supabase.py

       Windows (PowerShell):
           $env:DATABASE_URL="postgresql://postgres:YOURPASSWORD@YOURHOST:5432/postgres"
           python migrate_to_supabase.py

       Mac/Linux:
           export DATABASE_URL="postgresql://postgres:YOURPASSWORD@YOURHOST:5432/postgres"
           python migrate_to_supabase.py

3. Make sure database.db (your current local data) is sitting in the same
   folder as this script and app.py.

This script is safe to run more than once — it uses "merge" (insert-or-
update by ID) so re-running it won't create duplicates.
"""

import os
import sqlite3
import sys

from sqlalchemy import text

from app import app, db, Student, Position, Candidate

SQLITE_SOURCE = os.path.join(os.path.dirname(__file__), "database.db")


def run():
    if "DATABASE_URL" not in os.environ:
        print("ERROR: DATABASE_URL is not set.")
        print("Set it to your Supabase connection string first — see the")
        print("instructions at the top of this file.")
        sys.exit(1)

    if not os.path.exists(SQLITE_SOURCE):
        print(f"ERROR: could not find {SQLITE_SOURCE}")
        print("Put your existing database.db next to this script and try again.")
        sys.exit(1)

    src = sqlite3.connect(SQLITE_SOURCE)
    src.row_factory = sqlite3.Row

    with app.app_context():
        print(f"Connecting to: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[-1]}")
        print("Creating tables if they don't exist yet...")
        db.create_all()

        print("Copying positions...")
        for row in src.execute("SELECT * FROM position"):
            db.session.merge(Position(id=row["id"], name=row["name"]))
        db.session.commit()

        print("Copying candidates...")
        for row in src.execute("SELECT * FROM candidate"):
            db.session.merge(Candidate(
                id=row["id"],
                name=row["name"],
                position_id=row["position_id"],
                votes=row["votes"],
            ))
        db.session.commit()

        print("Copying students...")
        for row in src.execute("SELECT * FROM student"):
            db.session.merge(Student(
                id=row["id"],
                name=row["name"],
                student_class=row["student_class"],
                has_voted=bool(row["has_voted"]),
            ))
        db.session.commit()

        # Postgres tracks the "next ID to use" separately from the rows
        # themselves. Since we just inserted rows with specific IDs by hand,
        # we need to tell Postgres to continue counting from the highest one
        # — otherwise the next student/position/candidate added through the
        # app could collide with one we just migrated.
        if db.engine.dialect.name == "postgresql":
            print("Syncing auto-increment counters...")
            for table in ("position", "candidate", "student"):
                db.session.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('\"{table}\"', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM \"{table}\"), 1))"
                ))
            db.session.commit()

        print()
        print("Done. Row counts now in the target database:")
        print("  Positions: ", Position.query.count())
        print("  Candidates:", Candidate.query.count())
        print("  Students:  ", Student.query.count())


if __name__ == "__main__":
    run()
