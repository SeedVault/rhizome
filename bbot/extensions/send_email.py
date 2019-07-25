""""""
import smtplib
import logging
from email.message import EmailMessage
from bbot.core import ChatbotEngine, BBotException, BBotLoggerAdapter



class SendEmail():
    """Sends email"""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.
        """
        self.config = config
        self.dotbot = dotbot

        self.logger_level = ''

        self.core = None
        self.logger = None

    def init(self, core: ChatbotEngine):
        """

        :param bot:
        :return:
        """
        self.core = core
        self.logger = BBotLoggerAdapter(logging.getLogger('core_ext.send_email'), self, self.core, '$sendEmail')        
        core.register_function('sendEmail', {'object': self, 'method': 'sendEmail', 'cost': 0.001, 'register_enabled': True})

    def sendEmail(self, args, f_type):
        """
        Sends email

        :param args:
        :param f_type:
        :return:
        """
        try:
            recipient = self.core.resolve_arg(args[0], f_type)
        except IndexError:
            raise BBotException({'code': 250, 'function': 'sendEmail', 'arg': 0, 'message': 'Recipient address is missing.'})

        try:
            sender = self.core.resolve_arg(args[1], f_type)
        except IndexError:
            raise BBotException({'code': 251, 'function': 'sendEmail', 'arg': 1, 'message': 'Sender address is missing.'})
        if type(recipient) is not str:
            raise BBotException({'code': 251, 'function': 'sendEmail', 'arg': 0, 'message': 'Recipient has to be string.'})

        try:
            subject = self.core.resolve_arg(args[2], f_type)
        except IndexError:
            raise BBotException({'code': 252, 'function': 'sendEmail', 'arg': 2, 'message': 'Subject is missing.'})
        if type(subject) is not str:
            raise BBotException({'code': 251, 'function': 'sendEmail', 'arg': 2, 'message': 'Subject has to be string.'})

        try:
            body = self.core.resolve_arg(args[3], f_type)
        except IndexError:
            raise BBotException({'code': 253, 'function': 'sendEmail', 'arg': 3, 'message': 'Email body is missing.'})

        smtp_config = self.core.dotbot['smtp']

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient

        body = body.replace('\n', '<br />')

        msg.set_content("Please see this email with an html compatible email client\n")
        msg.add_alternative(f"""\
                    <html>
                    <head></head>
                        <body>
                            {body}
                        </body>
                    </html>
                    """, subtype='html')

        self.logger.debug(
            f"Sending email through {smtp_config['server_host']}:{smtp_config['server_port']} to {recipient}")

        smtp = smtplib.SMTP(smtp_config['server_host'], smtp_config['server_port'])
        smtp.set_debuglevel(1)
        if smtp_config.get('server_username', "") and smtp_config.get('serer_password', ""):
            smtp.login(smtp_config['server_username'], smtp_config['server_password'])
        smtp.send_message(msg)
        smtp.quit()
