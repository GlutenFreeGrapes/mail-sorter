from ast import literal_eval
import sys

import webbrowser
urL='https://www.google.com'
chrome_path="C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
webbrowser.register('chrome', None,webbrowser.BackgroundBrowser(chrome_path),preferred=1)
webbrowser.get('chrome').open_new_tab(urL)

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import math

with open(sys.argv[1]) as f:
    email_categories = literal_eval(f.read())
    all_emails = set()
    for emails in email_categories.values():
        all_emails.update(emails)
    all_emails = list(all_emails)

    SCOPES=["https://www.googleapis.com/auth/gmail.modify"]
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES)
    flow.run_local_server(port=0)
    credentials = flow.credentials
    service = build("gmail", "v1", credentials= credentials)
    results = service.users().labels().list(userId="me").execute()
    print(results)
    try: 
        # in batches of 1000
        IGNORE_LABELS = ["SENT", "DRAFT", "CHAT"]
        labels_to_remove = list({label["id"] for label in results.get("labels", [])} - set(IGNORE_LABELS))
        for i in range(math.ceil(len(all_emails)/1000)):
            body = {"ids":all_emails[i*1000: (i+1)*1000], "removeLabelIds": [labels_to_remove]}
            service.users().messages().batchModify(userId = "me", body=body).execute()
        print(f"{len(all_emails)} messages with labels removed.")

        for new_label in email_categories:
            message_ids = list(email_categories[new_label])
            for i in range(math.ceil(len(message_ids)/1000)):
                body = {"ids":message_ids[i*1000: (i+1)*1000], "addLabelIds": [new_label]}
                service.users().messages().batchModify(userId = "me", body=body).execute()
            print(f"{len(message_ids)} messages moved to {new_label}.")
    except HttpError as error:
        print(f"An error occurred: {error}")

