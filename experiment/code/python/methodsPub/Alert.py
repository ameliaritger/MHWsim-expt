import smtplib

smtp_username = "805raspberrypi@gmail.com" # This is the username used to login to your SMTP provider
smtp_password = "oqpp jtad dknv mnsn" # This is the password used to login to your SMTP provider
smtp_host = "smtp.gmail.com" # This is the host of the SMTP provider
smtp_port = 587 # This is the port that your SMTP provider uses

sender = "805raspberrypi@gmail.com"
receiver = ["7757818224@vtext.com"] # must be a list

subject = "Beep Boop!"

text = "Amelia's Raspberry Pi is trying to get your attention!"

# Prepare actual message

message = """\
From: %s
To: %s
Subject: %s

%s
""" % (sender, ", ".join(receiver), subject, text)

def send_email():
    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        # identify ourselves to smtp gmail client
        server.ehlo()
        # secure our email with tls encryption
        server.starttls()
        # re-identify ourselves as an encrypted connection
        server.ehlo()
        server.login(smtp_username, smtp_password) # If you don't need to login to your smtp provider, simply remove this line
        server.sendmail(sender, receiver, message)         
        print("Successfully sent email")
        server.quit()
    except smtplib.SMTPException:
        print("Error: unable to send email")