#!/usr/bin/env python3

"""Example code for uploading a local folder of files to Dropbox using the Dropbox API in a performant manner."""

from concurrent.futures import ThreadPoolExecutor

import argparse
import logging
import os
import time

import dropbox

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

MB = 1024 * 1024

parser = argparse.ArgumentParser(description='Upload a folder of files to Dropbox in a performant manner.')
parser.add_argument('--local_path', required=True, help='Local path of folder of files to upload (non-recursive).')
parser.add_argument('--remote_path', required=True, help='Remote path of folder in Dropbox to upload to.')
parser.add_argument('--access_token', help='Access token to use to perform the API calls.')
parser.add_argument('--refresh_token', help='Refresh token to use to retrieve access tokens.')
parser.add_argument('--app_key', help='App key to use to retrieve access tokens. Required when using a refresh token.')
parser.add_argument('--app_secret', help='App secret to use to retrieve access tokens.')

# These three values can be tuned for better (or worse) overall performance, based on the scenario and environment:
parser.add_argument('--chunk_size', default=24*MB, help='The amount of data, in bytes, to send per upload request.')
parser.add_argument('--batch_thread_count', default=20, help='How many threads to use per batch of upload sessions.')
parser.add_argument('--concurrent_thread_count', default=10, help='How many threads to use per upload session.')


def get_client(args):
    """Returns the Dropbox client to use to upload files."""

    if not (args.access_token or args.refresh_token):
        raise Exception("Either an access token or refresh token/app is key required.")

    if args.refresh_token:
        if not args.app_key:
            raise Exception("App key is required when using a refresh token.")
        return dropbox.Dropbox(
            oauth2_refresh_token=args.refresh_token,
            app_key=args.app_key,
            app_secret=args.app_secret  # the app secret is required for refresh tokens not acquired using PKCE
        )

    return dropbox.Dropbox(oauth2_access_token=args.access_token)


def collect_files(folder_path):
    """Returns the list of files to upload."""

    folder_path = os.path.expanduser(folder_path)

    # List all of the files inside the specified folder.
    files = sorted(
        [os.path.join(folder_path, f)
         for f in os.listdir(folder_path)
         if os.path.isfile(os.path.join(folder_path, f))  # ignores folders
         and f not in [".DS_Store", ".localized", ".gitignore"]  # ignores system files, etc.
         ]
    )

    logging.info(f"Collected {str(len(files))} files for upload: {files}")

    return files


def upload_session_appends(client, session_id, source_file_path, args):
    """Performs parallelized upload session appends for one file."""

    futures = []

    dest_file_name = os.path.basename(source_file_path)
    dest_folder = args.remote_path.lstrip("/")

    logging.info(f"Using upload session with ID '{session_id}' for file '{dest_file_name}'.")

    with open(source_file_path, "rb") as local_file:

        file_size = os.path.getsize(source_file_path)

        def append(dest_file_name, data, cursor, close):
            logging.debug(f"Appending to upload session with ID '{cursor.session_id}' for file '{dest_file_name}'"
                          f" at offset: {str(cursor.offset)}")
            client.files_upload_session_append_v2(f=data,
                                                  cursor=cursor,
                                                  close=close)
            logging.debug(f"Done appending to upload session with ID '{cursor.session_id}' for file '{dest_file_name}'"
                          f" at offset: {str(cursor.offset)}")

        if file_size > 0:  # For non-empty files, start a number of concurrent append calls.
            with ThreadPoolExecutor(max_workers=args.concurrent_thread_count) as session_executor:
                while local_file.tell() < file_size:
                    cursor = dropbox.files.UploadSessionCursor(session_id=session_id, offset=local_file.tell())
                    data = local_file.read(args.chunk_size)
                    close = local_file.tell() == file_size
                    futures.append(session_executor.submit(append, dest_file_name, data, cursor, close))
        else:  # For empty files, just call append once to close the upload session.
            cursor = dropbox.files.UploadSessionCursor(session_id=session_id, offset=0)
            append(dest_file_name=dest_file_name, data=None, cursor=cursor, close=True)

        for future in futures:
            try:
                future.result()
            except Exception as append_exception:
                logging.error(f"Upload session with ID '{cursor.session_id}' failed.")
                raise append_exception

        return dropbox.files.UploadSessionFinishArg(
            cursor=dropbox.files.UploadSessionCursor(session_id=session_id, offset=local_file.tell()),
            commit=dropbox.files.CommitInfo(path=f"/{dest_folder}/{dest_file_name}"))


def upload_files(client, files, args):
    """Performs upload sessions for a batch of files in parallel."""

    futures = []
    entries = []
    uploaded_size = 0

    assert len(entries) <= 1000, "Max batch size is 1000."
    assert args.chunk_size % (4 * MB) == 0, "Chunk size must be a multiple of 4 MB to use concurrent upload sessions"

    logging.info(f"Starting batch of {str(len(files))} upload sessions.")
    start_batch_result = client.files_upload_session_start_batch(
        num_sessions=len(files),
        session_type=dropbox.files.UploadSessionType.concurrent)

    with ThreadPoolExecutor(max_workers=args.batch_thread_count) as batch_executor:
        for index, file in enumerate(files):
            futures.append(
                batch_executor.submit(upload_session_appends, client, start_batch_result.session_ids[index], file, args)
            )

    for future in futures:
        entries.append(future.result())
        uploaded_size += future.result().cursor.offset

    logging.info(f"Finishing batch of {str(len(entries))} entries.")
    finish_launch = client.files_upload_session_finish_batch(entries=entries)

    if finish_launch.is_async_job_id():
        logging.info(f"Polling for status of batch of {str(len(entries))} entries...")
        while True:
            finish_job = client.files_upload_session_finish_batch_check(async_job_id=finish_launch.get_async_job_id())
            if finish_job.is_in_progress():
                time.sleep(.5)
            else:
                complete = finish_job.get_complete()
                break
    if finish_launch.is_complete():
        complete = finish_launch.get_complete()
    elif finish_launch.is_other():
        raise Exception("Unknown finish result type!")

    logging.info(f"Finished batch of {str(len(entries))} entries.")

    for index, entry in enumerate(complete.entries):
        if entry.is_success():
            logging.info(f"File successfully uploaded to '{entry.get_success().path_lower}'.")
        elif entry.is_failure():
            logging.error(f"Commit for path '{entries[index].commit.path}' failed due to: {entry.get_failure()}")

    return uploaded_size


def run_and_time_uploads():
    """Performs and times the uploads for the folder of files."""

    args = parser.parse_args()

    client = get_client(args=args)
    files = collect_files(folder_path=args.local_path)

    start_time = time.time()
    uploaded_size = upload_files(client=client, files=files, args=args)
    end_time = time.time()

    time_elapsed = end_time - start_time
    logging.info(f"Uploaded {uploaded_size} bytes in {time_elapsed:.2f} seconds.")

    megabytes_uploaded = uploaded_size / MB
    logging.info(f"Approximate overall speed: {megabytes_uploaded / time_elapsed:.2f} MB/s.")


if __name__ == '__main__':
    run_and_time_uploads()
