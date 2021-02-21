"""Sandbox file to play around with the APIs.
"""

import base64

import dcp_service
import download_helper
import html_service

from absl import app


def main(argv):
    gmail_svc = download_helper.init_and_get_gmail_service()

    ids, _ = gmail_svc.search_messages('Subject:(Daily Coding Problem: Problem #761)')
    # ids, _ = gmail_svc.search_messages('Subject:(Daily Coding Problem: Solutions to Previous Problems)')
    print(ids)

    msg = gmail_svc.get_message_content(ids[0])
    print(msg.keys())

    subject = gmail_svc.get_message_subject(msg)
    print(subject)

    print('Body:')
    print(msg['body'])

    print('Parts')
    print('There are %d parts' % len(msg['parts']))

    # for part in msg['parts']:
    #     print(part['mimeType'])
    #     print(base64.urlsafe_b64decode(part['body']['data']))

    dcp_svc = dcp_service.DCP_Service(gmail_svc)
    txt_msg = dcp_svc.get_text_message(ids[0])
    # print(txt_msg)

    links = dcp_svc.get_solution_links_from_text(txt_msg)

    html_svc = html_service.Html_Service()
    for link in links:
        api_link = html_svc.get_api_link_from_href(link)
        print(html_svc.get_api_content_as_md(api_link))


if __name__ == '__main__':
    app.run(main)




