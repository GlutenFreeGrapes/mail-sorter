from bayes_model import Classifier
from email_reader import MailReader
import sys, pandas as pd, os
from collections import defaultdict

def sort_email(credentials, service):
    mailreader = MailReader(credentials, service)

    email_data = mailreader.readEmails()
    # print(email_data)
    # email_data.to_csv('emails.csv')

    classifier = Classifier(email_data)

    # classifier.print_classifier("email_classifier.txt")

    new_labels = defaultdict(set)
    changes = 0
    done = 0
    for idx, row in email_data.iterrows():
        predicted_label, probability = classifier.predict(row["content"])
        new_labels[predicted_label].add(row["id"])
        done+=1
        if not done%100:
            print(done)
        if predicted_label != row["tag"]:
            changes+=1

    # print(f"{changes} emails to be reclassified")

    for label in new_labels:
        mailreader.relabelMessages(list(new_labels[label]), label)
    # print("emails moved")
    return new_labels