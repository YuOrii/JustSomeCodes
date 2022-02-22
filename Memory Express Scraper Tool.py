from datetime import datetime
from time import sleep
from imap_tools import MailBox, AND

import requests
import smtplib
import ssl
from bs4 import BeautifulSoup

location = str(sys.argv[1])
# Locations are NW, SE, NE for Calgary!!
url = "https://www.memoryexpress.com/Category/VideoCards?InventoryType=InStock&Inventory=Cal" + location

# emailing information
port = 465
context = ssl.create_default_context()
sender = f"Enter Sender Email (GMail): "
recipients = input(f"Enter Recipients ")
pw = input(f"Password for {sender}: ")

server = smtplib.SMTP_SSL("smtp.gmail.com", port, context=context)
server.login(sender, pw)
print(f'Signed in to {sender} sucessfully!')

buffer_list = []

while True:
    try:
        # Get HTML
        html = requests.get(url).text
        soup = BeautifulSoup(html, "html.parser")

        # Prepare email
        time = (datetime.now())
        mail_content = ""

        # Get total number of available products
        n = (soup.find("header", attrs={"data-role": "filter-blurb"})).find("span").text
        print("found: " + n)

        # Get list of product
        products = soup.find_all("div", attrs={"class": "c-shca-icon-item__body-name"})
        product_list = []

        # Import product to lsit
        for i in products:
            k = i.find_next("a")
            product_list.append(k.text.strip().replace("\n", " ").replace("™", "") + "\n --------------- \n")

        # Compare with last list
        difference_list = list(set(product_list).symmetric_difference(set(buffer_list)))
        print(f"difference: {len(difference_list)}")

        # Determine the number of products being changed
        if len(buffer_list) < len(product_list):
            print(f'{time}: NEW ARRIVAL!!!')
            mail_content = f"Subject: NEW ARRIVAL @ {location} !!!\n\n\n"
        elif len(buffer_list) > len(product_list):
            print(f'{time}: Sold out???')
            mail_content = f"Subject: Sold Out @ {location} ???\n\n\n"
        else:
            print(f'{location}: {time}: no change :((')

        # Send email when there is change
        if len(difference_list) > 0:
            mail_content += f'\n{len(difference_list)} / {n} items changed \n'
            for i in difference_list:
                mail_content = mail_content + "\n" + i
            mail_content += url
            mail_content += time
            server.sendmail(sender, recipients, mail_content)
            print(f"Email Sent: {mail_content}")

        # Clear lists for next iteration
        buffer_list = product_list
        difference_list.clear()
        sleep(5)

        # Check for new email and send status
        have_mail = False
        mb = MailBox('imap.gmail.com').login(sender, pw, 'INBOX')
        inbox = mb.fetch(criteria=AND(subject=location, seen=False), mark_seen=True)
        for i in inbox:
            print(f"Mail Found: {i.from_}{i.subject}")
            have_mail = True
        if have_mail:
            mail_content = f"Subject: Live check @ {location}... \n\n{time}\n\n"
            mail_content += f"{len(product_list)} items found\n\n"
            for i in product_list:
                mail_content += i + '\n'
            server.sendmail(sender, recipients, mail_content)

    # Catch network errors
    except ConnectionResetError as ignored:
        pass
    except ConnectionError as ignored:
        pass
    except TimeoutError as ignored:
        pass
