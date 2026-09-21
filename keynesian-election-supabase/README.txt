Keynesian Institute — Digital Election System
==============================================

HOW TO RUN
-----------
1. Open a terminal in this folder.
2. Install dependencies:
       pip install -r requirements.txt
3. Start the app:
       python app.py
4. Open your browser to:
       http://127.0.0.1:5000

LOGINS
------
Admin login:   username = admin   password = 1234
Student login: use the Name + Class of any student you've added
               in the Students page (admin side) first.

TYPICAL FLOW TO TEST IT
------------------------
1. Go to /admin, log in with admin / 1234.
2. Go to Positions -> add a position (e.g. "Head Boy").
3. Go to Candidates -> add a candidate under that position.
4. Go to Students -> add a student (e.g. Name: Ali, Class: A2).
5. Log out (close the tab) and go to the home page ("/").
6. Click "Student Login" -> log in as the student you just added.
7. Cast a vote -> you'll land on the success page.
8. Go back to /admin -> Results to see the live vote bars.
9. "Reset Election" on the Results page clears all votes and
   lets every student vote again.

NOTES
-----
- Uses SQLite; a database.db file will be created automatically
  next to app.py the first time you run it.
- Add your own logo at static/images/logo.png.jpeg and it'll
  appear automatically in the sidebar/login screens — otherwise
  a "KI" badge is shown instead.
- "Upload Excel" on the Students page expects columns named
  exactly "Name" and "Class".
