#!/usr/bin/env python3

import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect

'''
This example uses PKCE, a currently beta feature.
If you are interested in using this, please contact
Dropbox support
'''
APP_KEY = ""

auth_flow = DropboxOAuth2FlowNoRedirect(APP_KEY, pkce_method='S256', token_access_type='offline')

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

dbx = dropbox.Dropbox(oauth2_refresh_token=oauth_result.refresh_token, app_key=APP_KEY)
dbx.users_get_current_account()
