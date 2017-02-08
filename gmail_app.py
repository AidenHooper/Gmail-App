from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import base64
from apiclient import errors
import re

try:
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
detach_dir = '.'
# SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'

ILLEGAL_NTFS_CHARS = "[<>:/\\|?*\"]|[\0-\31]"


def __removeIllegalChars(name):
    # removes characters that are invalid for NTFS
    return re.sub(ILLEGAL_NTFS_CHARS, "", name)


def ListMessagesWithLabels(service, user_id, label_ids=[]):
    try:
        response = service.users().messages().list(userId=user_id,
                                                   labelIds=label_ids).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id,
                                                       labelIds=label_ids,
                                                       pageToken=page_token).execute()
            messages.extend(response['messages'])

        for message in messages[:20]:
            getMessageDetails(service, user_id, message.get('threadId'))

    except errors.HttpError, error:
        print('An error occurred: %s') % error


def getMessageDetails(service, user_id, msg_id, prefix="peto_"):
    try:
        is_plain_text_email = False
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()
        if not message.get('payload'):
            return
        if not message['payload'].get('parts'):
            if not [
            header.get('value') for header in message.get('payload').get('headers') if "text/plain" in header.get('value') and header.get('name') == "Content-Type"]:
                return
            else:
                is_plain_text_email = True
        subject = next(
            header.get('value') for header in message.get('payload').get('headers') if header.get('name') in ['Subject', 'subject'])

        # create dir with subject line
        if __removeIllegalChars(subject) not in os.listdir("%s" % detach_dir):
            os.mkdir('%s' % __removeIllegalChars(subject))

        # handle if email is plain text with no attachment
        if is_plain_text_email:
            data = message.get('payload', {}).get('body', {}).get('data')
            file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
            path = prefix + subject + ".html"
            filePath = os.path.join(__removeIllegalChars(subject), path)
            with open(filePath, 'wb') as f:
                f.write(file_data)
        else:
            for part in message['payload'].get('parts'):
                if part['filename']:
                    if 'data' in part['body']:
                        data = part['body']['data']
                    else:
                        att_id = part['body']['attachmentId']
                        att = service.users().messages().attachments().get(userId=user_id, messageId=msg_id,
                                                                           id=att_id).execute()
                        data = att['data']
                    file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                    path = prefix + part['filename']
                    filePath = os.path.join(__removeIllegalChars(subject), path)
                    with open(filePath, 'wb') as f:
                        f.write(file_data)

                else:
                    s_part = [s_part for s_part in part.get('parts', []) if s_part.get('mimeType', '') in ["text/html", 'text/plain']]
                    if not s_part:
                        if part.get('mimeType', '') in ["text/html", 'text/plain']:
                            data = part.get('body', {}).get('data')
                        else:
                            continue
                    else:
                        part = s_part[0]
                        data = part.get('body', {}).get('data')
                    if data:
                        file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                        path = prefix + subject + ".html"
                        filePath = os.path.join(__removeIllegalChars(subject), path)
                        with open(filePath, 'wb') as f:
                            f.write(file_data)
        message = service.users().messages().modify(userId=user_id, id=msg_id, body={'removeLabelIds': ['Label_7'], 'addLabelIds': ['Label_16']}).execute()

    except errors.HttpError, error:
        print('An error occurred: %s' % errors)


def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credential1s')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def get_labels(service, user_id):
    results = service.users().labels().list(userId=user_id).execute()
    labels = results.get('labels', [])
    if not labels:
        print('No labels found.')
        return None
    else:
        return labels


def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    ListMessagesWithLabels(service, 'me', ["Label_7"])
    # print (get_labels(service, 'me'))


if __name__ == '__main__':
    main()
