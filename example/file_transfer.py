#!/usr/bin/env python

"""Reliable upload and download example.

Set DROPBOX_ACCESS_TOKEN before running this example. Override the paths with
DROPBOX_DOWNLOAD_PATH, LOCAL_DOWNLOAD_PATH, DROPBOX_UPLOAD_PATH, and
LOCAL_UPLOAD_PATH as needed.
"""

from __future__ import print_function

import os

import dropbox
from dropbox import files
from dropbox.file_transfer import (
    DownloadOptions,
    Downloader,
    File,
    FileUpload,
    UploadOptions,
    Uploader,
)


def required_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError("{} is required".format(name))
    return value


def print_download_progress(progress):
    print(
        "\rDownloaded {} of {} bytes".format(
            progress.bytes_committed,
            progress.total_bytes,
        ),
        end="",
    )


def print_upload_progress(progress):
    print(
        "\rUploaded {} of {} bytes".format(
            progress.bytes_committed,
            progress.total_bytes,
        ),
        end="",
    )


def main():
    dbx = dropbox.Dropbox(required_env("DROPBOX_ACCESS_TOKEN"))

    download_result = Downloader(dbx).download(
        os.environ.get("DROPBOX_DOWNLOAD_PATH", "/large-file.bin"),
        File(os.environ.get("LOCAL_DOWNLOAD_PATH", "large-file.bin")),
        DownloadOptions(
            parallel_downloads=int(os.environ.get("DROPBOX_PARALLEL_DOWNLOADS", "1")),
            progress=print_download_progress,
        ),
    )
    print("\nDownloaded {}".format(download_result.metadata.path_display))

    upload_result = Uploader(dbx).upload(
        FileUpload(os.environ.get("LOCAL_UPLOAD_PATH", "large-file.bin")),
        files.CommitInfo(
            os.environ.get("DROPBOX_UPLOAD_PATH", "/large-file-uploaded.bin"),
            mode=files.WriteMode.overwrite,
        ),
        UploadOptions(
            parallel_uploads=int(os.environ.get("DROPBOX_PARALLEL_UPLOADS", "1")),
            progress=print_upload_progress,
        ),
    )
    print("\nUploaded {}".format(upload_result.metadata.path_display))


if __name__ == "__main__":
    main()
