import smtplib

class mailclient:

    def __init__(self, user, password, server, port):
        self.user = user
        self.password = password
        self.server = server
        self.port = port

    def sendmail(text):

        user = ''
        password = ''

        sent_from = user
        to = ['']
        subject = 'freie Termine'
        body = text

        email_text = """\
        From: %s
        To: %s
        Subject: %s

        %s
        """ % (sent_from, ", ".join(to), subject, body)

        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(user, password)
            server.sendmail(sent_from, to, email_text)

            server.close()

            print('Email sent!')
        except:
            print('Something went wrong...')
