import time
import smtplib
from email.message import EmailMessage
from constants import TIME_LOCK_PERIOD


class Watchtower:
    def __init__(self):
        self.monitored_channels = {}  # Key: channel_id, Value: channel_record

    def monitor_channel(self, channel, latest_transaction, signatures):
        self.monitored_channels[channel.id] = {
            'channel': channel,
            'latest_transaction': latest_transaction,
            'signatures': signatures
        }

    def check_channels(self):
        current_time = time.time()
        for channel_id, record in self.monitored_channels.items():
            channel = record['channel']
            if channel.close_requested:
                time_since_request = current_time - channel.close_request_time
                if time_since_request < TIME_LOCK_PERIOD:
                    if record['latest_transaction'].index > channel.last_transaction_index:
                        self.challenge_close(channel, record['latest_transaction'], record['signatures'])
                else:
                    self.notify_user_of_close(channel)

    def challenge_close(self, channel, latest_transaction, signatures):
        # In a real-world scenario, this would involve submitting the challenge to the blockchain
        # Here, we'll just update the channel directly and print a message
        channel.challenge_close(latest_transaction.index)
        print(f"Challenged close for channel {channel.id} with transaction {latest_transaction.index}")

    def notify_user_of_close(self, channel):
        # Send an email notification to the user
        self.send_email_notification(f"Channel {channel.id} Closed", f"Channel {channel.id} has been closed.")

    def send_email_notification(self, subject, body):
        # This is a basic implementation using smtplib; you'd need to set up your SMTP server details
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = 'watchtower@example.com'
        msg['To'] = 'user@example.com'  # This should be the user's email address

        # Connect to the SMTP server and send the email
        with smtplib.SMTP('smtp.example.com', 587) as server:
            server.login('watchtower@example.com', 'password')  # Use your SMTP server credentials
            server.send_message(msg)