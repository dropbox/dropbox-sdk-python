#!/usr/bin/env python3

import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect

APP_KEY = ""
APP_SECRET = ""

auth_flow = DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET)

authorize_url = auth_flow.start()
print("1. Go to: " + authorize_url)
print("2. Click \"Allow\" (you might have to log in first).")
print("3. Copy the authorization code.")
auth_code = input("Enter the authorization code here: ").strip()

try:
    oauth_result = auth_flow.finish(auth_code)
    print(oauth_result)
except Exception as e:
    print('Error: %s' % (e,))
    exit(1)

dbx = dropbox.Dropbox(oauth2_access_token=oauth_result.access_token,
                      app_key=APP_KEY, app_secret=APP_SECRET)
dbx.users_get_current_account()
