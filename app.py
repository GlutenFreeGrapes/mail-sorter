from googleapiclient.discovery import build

from oauth2client.client import OAuth2WebServerFlow, AccessTokenCredentials

from flask import Flask, render_template, session, request, redirect, url_for,jsonify

from bayes_model import Classifier
from email_reader import MailReader
import os
from collections import defaultdict

app = Flask(__name__)


@app.route('/login')
def login():
  flow = OAuth2WebServerFlow(client_id=os.environ.get("CLIENT_ID"),
    client_secret=os.environ.get("CLIENT_SECRET"),
    scope='https://www.googleapis.com/auth/gmail.modify',
    redirect_uri='http://localhost:5000/oauth2callback',
    approval_prompt='force',
    access_type='offline')

  auth_uri = flow.step1_get_authorize_url()
  return redirect(auth_uri)

@app.route('/signout')
def signout():
  del session['credentials']
  session['message'] = "You have logged out"

  return render_template("signout.html")
  # return redirect(url_for('index'))

@app.route('/oauth2callback')
def oauth2callback():
  code = request.args.get('code')
  if code:
    # exchange the authorization code for user credentials
    flow = OAuth2WebServerFlow(os.environ.get("CLIENT_ID"),
      os.environ.get("CLIENT_SECRET"),
      "https://www.googleapis.com/auth/gmail.modify")
    flow.redirect_uri = request.base_url

    try:
      credentials = flow.step2_exchange(code)
    except Exception as e:
      print ("Unable to get an access token because ", e.message)

    # store these credentials for the current user in the session
    # This stores them in a cookie, which is insecure. Update this
    # with something better if you deploy to production land
    session['credentials'] = credentials.access_token
    session['user-agent'] = credentials.user_agent
  return redirect(url_for('index'))

@app.route('/')
def index():
  if 'credentials' not in session:
    return redirect(url_for('login'))
  credentials = AccessTokenCredentials(session['credentials'],session['user-agent'])
  service = build("gmail", "v1", credentials=credentials)

  user =service.users().getProfile(userId="me").execute().get("emailAddress")
  session['user-email'] = user

  return render_template("index.html", user=user)

@app.route('/sort-start')
def start_sort():
  return render_template('sorting.html')

@app.route('/sort')
def mail_sort():
  credentials = AccessTokenCredentials(session['credentials'],session['user-agent'])
  service = build("gmail", "v1", credentials=credentials)
  mailreader = MailReader(credentials, service)
  email_data = mailreader.readEmails()

  classifier = Classifier(email_data)

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

  for label in new_labels:
    mailreader.relabelMessages(list(new_labels[label]), label)
  return jsonify("sorting msgs")

@app.route('/done')
def done():
  return render_template('done.html')

if __name__ == '__main__':
  app.secret_key = 'hello world'
  app.run(host='0.0.0.0')