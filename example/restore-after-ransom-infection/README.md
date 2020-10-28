# Restore after ransom infection
## A Dropbox API sample app to show Python SDK and get rid of ransom in your dropbox

# How to run
Make sure you've installed the Dropbox Python SDK by following the installation instructions ( https://www.dropbox.com/developers/documentation/python#install ). 

Then, find this line in restore-after-ransom-infection.py and modify it to include your own access token. 
```TOKEN = ''```

From the example/backup-and-restore directory, run the script.
```python3 restore-after-ransom-infection.py```

# Description
## Functionality
1. Gather files encrypted by a ransomwhere.
Once encrypted a new encrypted copy of your files is saved into your dropbox; whereas the original copy is flagged as to be deleted. Your only task here is to identify the new extension (*.rap in my case) and to change the code accordingly.

2. For each file matching the regular expression the script gathers the latest revision of the original file and restores it if still flagged as deleted. 

# API usage
## New v2 endpoints
This app uses the Dropbox API v2 endpoints files_list_folder, files_list_folder_continue, files_list_revisions, files_restore and files_delete.