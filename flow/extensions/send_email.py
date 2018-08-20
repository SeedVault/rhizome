"""Send emails."""
import smtplib
from email.message import EmailMessage
from jinja2 import Template
from flow.engine import Extension

class SendEmail(Extension):
    """SendEmail plugin - defined .flow function sendEmail to send emails."""

    def __init__(self, flow):
        super().__init__(flow)
        class_name = self.__class__.__module__ + '.' + self.__class__.__name__
        flow.register_dot_flow_function('sendEmail', {
            'class': class_name, 'method': 'sendEmail'})


    def match(self, node):
        """Send  email."""
        params = dict()
        if node['info']['formId']: # if there is a form defined, send the form too
            form = self.flow.session.get(f"formVars.{node.info.formId}")  # <!-- @TODO Check this
            # build form
            for item in form:
                params[item['question'][0]] = item['answer']  # <!-- @TODO Check this
        # takes email data from node
        body_template = Template(node['info']['body'])
        subject_template = Template(node['info']['subject'])
        msg = EmailMessage()
        msg['Subject'] = subject_template.render(params)
        msg['From'] = self.flow.dotbot.bot.senderEmailAddress # <!-- @TODO Check this
        msg['To'] = node['info']['recipient']
        msg.set_content(body_template.render(params))
        smtp = smtplib.SMTP('localhost')
        smtp.send_message(msg)
        smtp.quit()
