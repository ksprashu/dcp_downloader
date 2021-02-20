"""Sandbox file to play around with the APIs.
"""

import base64

import download_helper

from absl import app


def main(argv):
    gmail_svc = download_helper.init_and_get_gmail_service()

    ids, _ = gmail_svc.search_messages('Subject:(Daily Coding Problem: Problem #761)')
    print(ids)

    msg = gmail_svc.get_message_content(ids[0])
    print(msg.keys())

    subject = gmail_svc.get_message_subject(msg)
    print(subject)

    print('Body:')
    print(msg['body'])

    print('Parts')
    print('There are %d parts' % len(msg['parts']))

    for part in msg['parts']:
        print(part['mimeType'])
        print(base64.urlsafe_b64decode(part['body']['data']))


if __name__ == '__main__':
    app.run(main)




