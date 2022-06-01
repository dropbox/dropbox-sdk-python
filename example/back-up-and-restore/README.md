# Backup And Restore
## A Dropbox API sample app for the Python SDK

# How to run
Make sure you've installed the Dropbox Python SDK by following the installation instructions ( https://www.dropbox.com/developers/documentation/python#install ). 

Then, find this line in backup-and-restore-sample.py and modify it to include your own access token. 
```TOKEN = ''```

From the example/backup-and-restore directory, run the script.
```python backup-and-restore-sample.py```

You should see the file my-file-backup.txt show up in the Dropbox account you used to get the access token.

# Description
## Functionality
1. Back up a file ("my-file.txt")
The my-file.txt file is a simple file that could be any kind of app or user data.
In this example, it contains a simple string of text (initially "original").

2. Restore a file to a previous version (using /revisions) 

# API usage
## New v2 endpoints
This app uses the Dropbox API v2 endpoints files_upload, files_restore, files_download_to_file, and files_list_revisions. See more here: http://dropbox-sdk-python.readthedocs.org/en/main/

## Error checking
This example also shows you how to do specific error handling with the new API v2 exceptions. In the backup() function, you can see how to check for a specific kind of API Error.