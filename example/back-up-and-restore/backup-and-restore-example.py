"""
Backs up and restores a settings file to Dropbox.
This is an example app for API v2.
"""

from __future__ import print_function

import sys

import dropbox
from dropbox.exceptions import ApiError, AuthError
from dropbox.files import WriteMode

# Add OAuth2 access token here.
# You can generate one for yourself in the App Console.
# See
# <https://blogs.dropbox.com/developers/2014/05/generate-an-access-token-for-your-own-account/>
TOKEN = ''

LOCALFILE = 'my-file.txt'
BACKUPPATH = '/my-file-backup.txt'

def backup():
    """
    Upload contents of LOCALFILE to Dropbox
    """
    with open(LOCALFILE, 'rb') as f:
        # We use WriteMode=overwrite to make sure that the settings in the file
        # are changed on upload
        print(
            "Uploading " +
            LOCALFILE +
            " to Dropbox as " +
            BACKUPPATH +
            "...")
        try:
            dbx.files_upload(f.read(), BACKUPPATH, mode=WriteMode('overwrite'))
        except ApiError as err:
            # This checks for the specific error where a user doesn't have
            # enough Dropbox space quota to upload this file
            if (err.error.is_path() and
                    err.error.get_path().error.is_insufficient_space()):
                sys.exit("ERROR: Cannot back up; insufficient space.")
            elif err.user_message_text:
                print(err.user_message_text)
                sys.exit()
            else:
                print(err)
                sys.exit()

def change_local_file(new_content):
    """
    Change the text string in LOCALFILE to be new_content
    Params: new_content:string
    Return: None
    """
    print("Changing contents of " + LOCALFILE + " on local machine...")
    with open(LOCALFILE, 'wb') as f:
        f.write(new_content)

def restore(rev=None):
    """
    Restore the file on Dropbox to a certain revision
    Params: rev:string - revision number
    Return: None
    """
    print("Restoring " + BACKUPPATH + " to revision " + rev + " on Dropbox...")
    dbx.files_restore(BACKUPPATH, rev)

    # Download the specific revision of the file at BACKUPPATH to LOCALFILE
    print(
        "Downloading current " +
        BACKUPPATH +
        " from Dropbox, overwriting " +
        LOCALFILE +
        "...")
    dbx.files_download_to_file(LOCALFILE, BACKUPPATH, rev)

def select_revision():
    """
    Get revisions for a file (sort by datetime object "server_modified")

    Params: None
    Return: Revisions in descending order by date modified
    """
    print("Finding available revisions on Dropbox...")
    entry_revisions = dbx.files_list_revisions(BACKUPPATH, limit=30)
    entries = entry_revisions.entries  # pylint: disable=no-member
    revisions = sorted(entries, key=lambda entry: entry.server_modified)

    for revision in revisions:
        print(revision.rev, revision.server_modified)

    # Return the oldest revision (first entry, because revisions was sorted
    # oldest:newest)
    return revisions[0].rev

if __name__ == '__main__':
    # Check for an access token
    if len(TOKEN) == 0:
        sys.exit("ERROR: Looks like you didn't add your access token. "
                 "Open up backup-and-restore-example.py in a text editor and "
                 "paste in your token in line 14.")

    # Create an instance of a Dropbox class, which can make requests to the
    # API.
    print("Creating a Dropbox object...")
    dbx = dropbox.Dropbox(TOKEN)

    # Check that the access token is valid
    try:
        dbx.users_get_current_account()
    except AuthError as err:
        sys.exit("ERROR: Invalid access token; try re-generating an "
                 "access token from the app console on the web.")

    # Create a backup of the current settings file
    backup()

    # Change the user's file, create another backup
    change_local_file("updated")
    backup()

    # Restore the local and Dropbox files to a certain revision
    to_rev = select_revision()
    restore(to_rev)

    print("Done!")
