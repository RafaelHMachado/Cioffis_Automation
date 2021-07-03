import os
import email, smtplib, ssl      # used the sending function
from datetime import date
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import stdiomask

import environment_handling

# This is for email testing purposes, prints to consol instead of sending email
class SMTP_Server():
    def __init__(self):
        smtp_server = "smtp.gmail.com"
        port = 587  # For starttls
        sender_email = input("Enter the gmail address you would like to send from (must be google gmail): ")
        password = input("Type your password and press enter: ")
        receiver_email = input("Enter the email address you would like to send to: ")

        utc_date = environment_handling.time_handler.current_time(self)
        date = environment_handling.time_handler.human_date(self, utc_date)
        subject = "Driver Report " + date
        body = "This is an automated generated message. Please do not reply.\n" \
               "See the attachment for the day report and statuses.\n\n" \
               "Thank you, have a nice day!"

        # Create a multipart message and set headers
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        # Add body to email
        message.attach(MIMEText(body, "plain"))

        # Add attachment
        os.chdir('..//Report_CSV')
        filename = "Driver_Report.xlsx"

        # Convert file to binary mode
        with open(filename, "rb") as attachment:
            # Add file as application/octet-stream
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        # Encode file in ASCII characters to send by email
        encoders.encode_base64(part)

        # Add header as key/value pair to attachment part
        part.add_header(
            "Content-Disposition",
            f"attachment; filename = {filename}",
        )

        # add attachment to message and convert message to string
        message.attach(part)
        text = message.as_string()

        # Log in to server using secure context and send email
        context = ssl.create_default_context()

        try:
            server = smtplib.SMTP(smtp_server, port)
            server.ehlo() # helo/ehlo are hello commands to the SMTP server to identify the connection
            server.starttls(context=context) # secure the connection
            server.ehlo() # Can be omitted
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, text)
        except Exception as e:
            # Print any error messages to stdout
            print(e)
        finally:
            server.quit()

def email_account():
    SMTP_Server()

def todays_date():
    # Get todays date in Month-Day-Year format
    current_date = date.today()
    year = str(current_date.year)
    month = str(current_date.month)
    day = str(current_date.day)

    refactored_date = month +'_'+ day +'_'+ year

    return refactored_date

if __name__ == "__cioffi_email__":
    conv_date = todays_date()
    email_account()
