SUPABASE + VERCEL DEPLOYMENT GUIDE
====================================
Keynesian Institute — Digital Election System

This turns your app from "running on my own laptop with a SQLite file"
into "running on the internet with a real database." Follow these in
order — don't skip ahead.


PART 1 — CREATE YOUR SUPABASE PROJECT
---------------------------------------
1. Go to https://supabase.com and sign up / log in.
2. Click "New Project".
3. Give it a name (e.g. "keynesian-election"), set a database
   password — WRITE THIS PASSWORD DOWN, you'll need it in a minute —
   and pick any region.
4. Wait about 1-2 minutes while it provisions.
5. Once it's ready, go to: Project Settings (gear icon) -> Database.
6. Find "Connection string" -> choose the "URI" tab.
7. Copy that string. It looks like:
       postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxx.supabase.co:5432/postgres
8. Replace [YOUR-PASSWORD] in that string with the real password
   from step 3.

Keep this full string somewhere safe — this is your DATABASE_URL.


PART 2 — MOVE YOUR EXISTING DATA INTO SUPABASE
-------------------------------------------------
This copies your current 357 students, 7 positions, and 15 candidates
from your local database.db into the new Supabase database.

1. Open a terminal INSIDE this project folder (the one with app.py).
2. Install the extra tools this step needs:
       pip install -r requirements.txt
3. Set your DATABASE_URL environment variable to the string from Part 1:

   Windows (cmd):
       set DATABASE_URL=postgresql://postgres:YOURPASSWORD@db.xxxx.supabase.co:5432/postgres

   Windows (PowerShell):
       $env:DATABASE_URL="postgresql://postgres:YOURPASSWORD@db.xxxx.supabase.co:5432/postgres"

   Mac/Linux:
       export DATABASE_URL="postgresql://postgres:YOURPASSWORD@db.xxxx.supabase.co:5432/postgres"

4. Run the migration script:
       python migrate_to_supabase.py

5. You should see something like:
       Copying positions...
       Copying candidates...
       Copying students...
       Done. Row counts now in the target database:
         Positions:  7
         Candidates: 15
         Students:   357

   If those numbers match what you had locally, your data is now
   safely in Supabase. You can re-run this script any time — it
   won't create duplicates.

6. (Optional double-check) In the Supabase dashboard, go to
   Table Editor — you should see "student", "position" and
   "candidate" tables with your real data in them.


PART 3 — TEST IT LOCALLY AGAINST SUPABASE (RECOMMENDED)
----------------------------------------------------------
Before deploying, make sure the app actually talks to Supabase
correctly from your machine:

1. With DATABASE_URL still set from Part 2, run:
       python app.py
2. Open http://127.0.0.1:5000/dashboard (log in as admin first:
   /admin, admin / 1234) — you should see the real counts
   (357 students, etc.) even though app.py never touched
   database.db this time. That confirms it's reading from Supabase.


PART 4 — PUT YOUR CODE ON GITHUB
------------------------------------
Vercel deploys from a GitHub repository, so your code needs to live
there first.

1. Go to https://github.com and create a new empty repository
   (e.g. "keynesian-election-system"). Don't add a README —
   keep it empty.
2. In your project folder terminal:
       git init
       git add .
       git commit -m "Initial commit"
       git branch -M main
       git remote add origin https://github.com/YOUR-USERNAME/keynesian-election-system.git
       git push -u origin main

   (If "git" isn't recognized, install Git from https://git-scm.com
   first, then repeat these commands.)

NOTE: database.db does not need to go to GitHub since Vercel will use
Supabase, not the local file. If you want to keep it out of the repo,
add a line saying "database.db" to a file named .gitignore before
running "git add .".


PART 5 — DEPLOY ON VERCEL
------------------------------
1. Go to https://vercel.com and sign up / log in (you can sign in
   with your GitHub account directly — easiest option).
2. Click "Add New..." -> "Project".
3. Select the GitHub repository you just pushed.
4. Before clicking Deploy, expand "Environment Variables" and add:
       Name:  DATABASE_URL
       Value: (paste your full Supabase connection string from Part 1)
5. Click "Deploy".
6. Wait for the build to finish — Vercel will give you a live URL
   like https://keynesian-election-system.vercel.app

Visit that URL — your app is now live on the internet, reading and
writing to your real Supabase database. Every vote cast there
updates instantly, same as it did locally.


TROUBLESHOOTING
-----------------
"ModuleNotFoundError" on Vercel:
    Make sure requirements.txt is in the root of your repo (it
    already is in this folder) and that you didn't rename it.

Dashboard shows 0 students after deploying:
    Double check the DATABASE_URL environment variable in Vercel
    (Project -> Settings -> Environment Variables) matches exactly
    what you used in Part 2 — a typo there is the most common cause.

"password authentication failed":
    Your Supabase database password has a typo, or contains a
    special character that needs escaping in the URL. You can reset
    the DB password from Project Settings -> Database in Supabase
    and generate a fresh connection string.

Changes made in the live site don't show up:
    Postgres updates immediately — there's no caching in this app.
    If something seems stale, hard-refresh your browser
    (Ctrl+Shift+R / Cmd+Shift+R).
