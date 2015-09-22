"""
Backs up and restores a settings file to Dropbox.
This is an example app for API v2. 
It uses the v2 endpoints files_upload, files_restore, files_download_to_file, and files_list_revisions.
In the backup() function, it demonstrates how to check for a specific kind of API Error.

The my-app-file.txt file is a simple file for a user's app data.
In the example, it starts out with a simple string of text, like this:

original

"""

import sys
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError

# Add OAuth2 access token here. 
# You can generate one for yourself in the App Console.
# See <https://blogs.dropbox.com/developers/2014/05/generate-an-access-token-for-your-own-account/>
TOKEN = ''

LOCALFILE = 'my-app-file.txt'
BACKUPPATH = '/my-file-backup.txt'

# Uploads contents of LOCALFILE to Dropbox
def backup():
    with open(LOCALFILE, 'r') as f:
        # We use WriteMode=overwrite to make sure that the settings in the file
        # are changed on upload
        try:
            dbx.files_upload(f, BACKUPPATH, mode=WriteMode('overwrite'))
        except ApiError as err:
            # This checks for the specific error where a user doesn't have
            # enough Dropbox space quota to upload this file
            if (err.error.is_path() and
                    err.error.get_path().error.is_insufficient_space()):
                sys.exit("Cannot back up; insufficient space.")
            elif err.user_message_text:
                print(err.user_message_text)
                sys.exit()
            else:
                print(err)
                sys.exit()

# Change the text string in LOCALFILE to be new_content
# @param new_content is a string
def change_app_file(new_content):
    with open(LOCALFILE, 'w') as f:
        f.write(new_content)

# Restore the local and Dropbox files to a certain revision
def restore(rev=None):
    # Restore the file on Dropbox to a certain revision
    dbx.files_restore(BACKUPPATH, rev)
    # Download the specific revision of the file at BACKUPPATH to LOCALFILE
    dbx.files_download_to_file(LOCALFILE, BACKUPPATH, rev)
    print("Restored to revision " + rev)

# Look at all of the available revisions on Dropbox, and return the oldest one
def select_revision():
    # Get the revisions for a file (and sort by the datetime object, "server_modified")
    revisions = sorted(dbx.files_list_revisions(BACKUPPATH, limit=30).entries,
                       key=lambda entry: entry.server_modified)

    print("Available backups:")
    for revision in revisions:
        print(revision.rev, revision.server_modified)

    # Return the oldest revision (first entry, because revisions was sorted oldest:newest)
    return revisions[0].rev

if __name__ == '__main__':
    # Create an instance of a Dropbox class, which can make requests to the API.
    dbx = dropbox.Dropbox(TOKEN)

    # Create a backup of the current settings file
    backup()

    # Change the app's file, create another backup
    change_app_file("updated")
    backup()

    # Restore the local and Dropbox files to a certain revision
    to_rev = select_revision()
    restore(to_rev)
