#!/usr/bin/env python3

import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect

'''
It goes through an example of requesting a starting scope,
and requesting more throughout the process
'''
APP_KEY = ""
APP_SECRET = ""

auth_flow = DropboxOAuth2FlowNoRedirect(APP_KEY,
                                        consumer_secret=APP_SECRET,
                                        token_access_type='offline',
                                        scope=['files.metadata.read'])

authorize_url = auth_flow.start()
print("1. Go to: " + authorize_url)
print("2. Click \"Allow\" (you might have to log in first).")
print("3. Copy the authorization code.")
auth_code = input("Enter the authorization code here: ").strip()

try:
    oauth_result = auth_flow.finish(auth_code)
    # Oauth token has files.metadata.read scope only
    assert oauth_result.scope == 'files.metadata.read'
except Exception as e:
    print('Error: %s' % (e,))
    exit(1)

# If an application needs write scopes now we can request the new scope with the auth flow
auth_flow2 = DropboxOAuth2FlowNoRedirect(APP_KEY,
                                         consumer_secret=APP_SECRET,
                                         token_access_type='offline',
                                         scope=['files.metadata.write'])

authorize_url = auth_flow2.start()
print("1. Go to: " + authorize_url)
print("2. Click \"Allow\" (you might have to log in first).")
print("3. Copy the authorization code.")
auth_code = input("Enter the authorization code here: ").strip()

try:
    oauth_result = auth_flow2.finish(auth_code)
    # Oauth token has files.metadata.write scope only
    assert oauth_result.scope == 'files.metadata.write'
except Exception as e:
    print('Error: %s' % (e,))
    exit(1)

# If an application needs a new scope but wants to keep the existing scopes,
# you can add include_granted_scopes parameter
auth_flow3 = DropboxOAuth2FlowNoRedirect(APP_KEY,
                                         consumer_secret=APP_SECRET,
                                         token_access_type='offline',
                                         scope=['files.content.read', 'files.content.write'],
                                         include_granted_scopes='user')

authorize_url = auth_flow3.start()
print("1. Go to: " + authorize_url)
print("2. Click \"Allow\" (you might have to log in first).")
print("3. Copy the authorization code.")
auth_code = input("Enter the authorization code here: ").strip()

try:
    oauth_result = auth_flow3.finish(auth_code)
    print(oauth_result)
    # Oauth token has all granted user scopes
    assert 'files.metadata.write' in oauth_result.scope
    assert 'files.metadata.read' in oauth_result.scope
    assert 'files.content.read' in oauth_result.scope
    assert 'files.content.write' in oauth_result.scope
    print(oauth_result.scope)  # Printing for example
except Exception as e:
    print('Error: %s' % (e,))
    exit(1)

with dropbox.Dropbox(oauth2_access_token=oauth_result.access_token,
                     oauth2_access_token_expiration=oauth_result.expires_at,
                     oauth2_refresh_token=oauth_result.refresh_token,
                     app_key=APP_KEY,
                     app_secret=APP_SECRET):
    print("Successfully set up client!")
