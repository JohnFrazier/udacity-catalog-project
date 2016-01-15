A cataloging application project for udacity.
===

This is an image viewing and cataloging application. It provides lists of
images by user, category, and recent items. Users are logged in by facebook
oauth. Categories exist so long as images use them. Images are stored in
./uploads, image metadata is stored in the db. A get request with json mime-type
is handled for many image views. An ATOM feed is available to show recently
added items. An ATOM feed can be seen at /recent_feed.xml and a link for it is in
page headers for browser plugins to detect.

Usage
=====

1. Confirm listening address and port in application.py

2. Required dependencies: 
    python2, flask, flask-sqlalchemy, sqlite, flask-WTF, wtforms

3. An application specific secret key is required in secrets/application_secret:
    python -c 'import random; import string; print "".join([random.SystemRandom().choice(string.digits + string.letters + string.punctuation) for i in range(100)])' > key

4. A facebook oauth project id is required in secrets/fb_client_secrets.json

5. python application.py
6. login with your facebook account and add items and images.

Unit Tests
=====
1. Run python application_tests.py
