import time
import datetime
import smtplib

sleep_measure = 1 #number of seconds to sleep between sampling (interval)

def save_and_sleep(m, temp_set, heater_status, avg_temps_all):
    all_temps = temp_set + heater_status + avg_temps_all
    m.save(all_temps) #save data to csv
    print(f"Temperatures saved, going to sleep for {sleep_measure} seconds...")
    heater_status, avg_temps_all = ([] for i in range(2) )#deletethe lists by re-initializing a blank list
    time.sleep(sleep_measure)
    today = datetime.datetime.today() #check the current date
    
    return avg_temps_all, today

smtp_username = "805raspberrypi@gmail.com" # This is the username used to login to your SMTP provider
smtp_password = "uuesginoekrotmcj" # This is the password used to login to your SMTP provider
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
    except smtplib.SMTPException:
        print("Error: unable to send email")
