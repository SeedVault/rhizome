""""""
import smtplib
import logging
from email.message import EmailMessage
from bbot.core import ChatbotEngine, BBotException
from engines.dotflow2.chatbot_engine import DotFlow2LoggerAdapter


class DotFlow2SendEmail():
    """Sends email"""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.
        """
        self.config = config
        self.dotbot = dotbot

        self.logger_level = ''

        self.bot = None
        self.logger = None

    def init(self, bot: ChatbotEngine):
        """

        :param bot:
        :return:
        """
        self.bot = bot
        self.logger = DotFlow2LoggerAdapter(logging.getLogger('df2_ext.send_email'), self, self.bot, '$sendEmail')
        bot.register_dotflow2_function('sendEmail', {'object': self, 'method': 'df2_sendEmail'})
        bot.register_template_function('sendEmail', {'object': self, 'method': 'df2_sendEmail'})

    def df2_sendEmail(self, args, f_type):
        """
        Sends email

        :param args:
        :param f_type:
        :return:
        """
        try:
            recipient = self.bot.resolve_arg(args[0], f_type)
        except IndexError:
            raise BBotException({'code': 250, 'function': 'sendEmail', 'arg': 0, 'message': 'Recipient address is missing.'})

        try:
            sender = self.bot.resolve_arg(args[1], f_type)
        except IndexError:
            raise BBotException({'code': 251, 'function': 'sendEmail', 'arg': 1, 'message': 'Sender address is missing.'})
        if type(recipient) is not str:
            raise BBotException({'code': 251, 'function': 'sendEmail', 'arg': 0, 'message': 'Recipient has to be string.'})

        try:
            subject = self.bot.resolve_arg(args[2], f_type)
        except IndexError:
            raise BBotException({'code': 252, 'function': 'sendEmail', 'arg': 2, 'message': 'Subject is missing.'})
        if type(subject) is not str:
            raise BBotException({'code': 251, 'function': 'sendEmail', 'arg': 2, 'message': 'Subject has to be string.'})

        try:
            body = self.bot.resolve_arg(args[3], f_type)
        except IndexError:
            raise BBotException({'code': 253, 'function': 'sendEmail', 'arg': 3, 'message': 'Email body is missing.'})

        smtp_config = self.bot.dotbot['smtp']

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
