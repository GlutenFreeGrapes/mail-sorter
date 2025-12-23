import webbrowser

import selenium.webdriver
urL='https://www.google.com'
chrome_path="C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
webbrowser.register('chrome', None,webbrowser.BackgroundBrowser(chrome_path),preferred=1)
webbrowser.get('chrome').open_new_tab(urL)

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import pandas as pd, re, base64, math, selenium

def processMessage(content):
    return re.sub("[^a-zA-Z0-9 ]","",content.lower())

class MailReader:
    def __init__(self, credentials, service):
        ignore_labels = ["SENT", "DRAFT"]
       
        self.credentials = credentials
        self.service = service
        results = self.service.users().labels().list(userId="me").execute()
        self.labels = [label["id"] for label in results.get("labels", []) if label not in ignore_labels]
        self.ignore_labels = ignore_labels
        
    def importEmails(self, email_dataset):
        self.label_to_messages = {}
        for label in self.labels:
            filtered = email_dataset[email_dataset["tag"] == label]
            self.label_to_messages[label] = set(filtered["id"])

    def readEmails(self):
        # try:
        # Call the Gmail API
            # gather msgs to ignore
            ignore_msgs = set()
            for ignore_label in self.ignore_labels:
                nextPageToken = ""
                while 1:
                    results = (
                        self.service.users().messages().list(userId="me", labelIds = [ignore_label], maxResults=500,pageToken = nextPageToken).execute()
                    )
                    messages = results.get("messages", [])
                    nextPageToken = results.get("nextPageToken")
                    for message in messages:
                        ignore_msgs.add(message["id"])                
                    # last page
                    if not nextPageToken:
                        break
            # print(f"ignoring {len(ignore_msgs)} messages")

            # allowed msgs
            self.label_to_messages = {}
            for label in self.labels:
                nextPageToken = ""
                msg_ids = set()
                while 1:
                    results = (
                        self.service.users().messages().list(userId="me", labelIds = [label], maxResults=500,pageToken = nextPageToken).execute()
                    )
                    messages = results.get("messages", [])
                    nextPageToken = results.get("nextPageToken")
                    for message in messages:
                        msg_ids.add(message["id"])
                    # last page
                    if not nextPageToken:
                        # print(label, len(msg_ids))
                        break
                self.label_to_messages[label] = msg_ids - ignore_msgs
            # open('email_labels_before.txt','w').write(str(self.label_to_messages))
            # remove all overlaps
            for l1 in sorted(self.label_to_messages.keys(), key = lambda x: len(self.label_to_messages[x])):
                for l2 in sorted(self.label_to_messages.keys(), key = lambda x: len(self.label_to_messages[x])):
                    if l1!=l2:
                        # subtract set from the larger one
                        if len(self.label_to_messages[l1]) > len(self.label_to_messages[l2]):
                            self.label_to_messages[l1] -= self.label_to_messages[l2]
                        else:
                            self.label_to_messages[l2] -= self.label_to_messages[l1]
            # print("after removing duplicates:")
            # for label in self.label_to_messages:
                # print(label, len(self.label_to_messages[label]))

            # get email content and create DF from it
            emails = []
            for label in self.label_to_messages:
                for message_id in self.label_to_messages[label]:
                    message_obj = self.service.users().messages().get(userId = "me", id = message_id, format = "raw").execute()
                    message_raw = message_obj["raw"] + '==' #padding
                    decoded_bytes = base64.urlsafe_b64decode(message_raw)
                    message_content = decoded_bytes.decode("utf-8")
                    # input (message_content)
                    emails.append([message_id, label, processMessage(message_content)])
                    
            emails_df = pd.DataFrame(emails, columns = ["id", "tag", "content"])
            return emails_df
                

        # except HttpError as error:
            # print(f"An error occurred: {error}")

    def relabelMessages(self, message_ids, new_label):
        # try: 
            # in batches of 1000
            for i in range(math.ceil(len(message_ids)/1000)):
                body = {"ids":message_ids[i*1000: (i+1)*1000], "addLabelIds": [new_label], "removeLabelIds": [label for label in self.labels if (label != new_label) and len(self.label_to_messages[label])]}
                self.service.users().messages().batchModify(userId = "me", body=body).execute()
            # print(f"{len(message_ids)} messages moved to {new_label}.")
        # except HttpError as error:
            # print(f"An error occurred: {error}")
