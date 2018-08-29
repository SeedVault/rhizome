"""Send emails."""
import smtplib
from email.message import EmailMessage
from jinja2 import Template
from flow.chatbot_engine import Extension

class SendEmail(Extension):
    """SendEmail plugin - defined .flow function sendEmail to send emails."""

    def __init__(self, flow):
        super().__init__(flow)
        class_name = self.__class__.__module__ + '.' + self.__class__.__name__
        flow.register_dot_flow_function('sendEmail', {
            'class': class_name, 'method': 'sendEmail'})


    def sendEmail(self, args):
        """Send  email."""
        
        node = args[0]        
        params = dict()
            
        smtp_config = self.flow.dotbot['bot']['smtp']
        flow_vars = self.flow.session.get_var(self.flow.user_id)
        
        msg = EmailMessage()
        
        msg['Subject'] = self.flow.template_engine.render(self.flow, node['info']['subject'], flow_vars)
        msg['From'] = smtp_config['email']
        msg['To'] = node['info']['recipient']
        
        body = self.flow.template_engine.render(self.flow, node['info']['body'], flow_vars)
        body = body.replace('\n', '<br />')
                
        if node['info'].get('formId', None): # if there is a form defined, build form and add it to the message body
            flow_form = self.flow.session.get(self.flow.user_id, f"formVars.{node['info']['formId']}")                            
            form_template = "{% for form, qa_pair in form_xxxxx.items() %}{{qa_pair.question}}: {{qa_pair.answer}}<br />{% endfor %}"
            body += "<br /><br />" + Template(form_template).render({'form_xxxxx': flow_form})
                    
            msg.set_content("Please see this email with an html compatible email client\n")
            msg.add_alternative(f"""\
            <html>
            <head></head>
                <body>
                    {body}
                </body>
            </html>
            """, subtype='html')

        self.flow.logger.debug(f"Sending email through {smtp_config['server']['host']}:{smtp_config['server']['port']} to {node['info']['recipient']}")

        smtp = smtplib.SMTP(smtp_config['server']['host'], smtp_config['server']['port'])
        smtp.set_debuglevel(1)
        if smtp_config['server'].get('username', "") and smtp_config['server'].get('password', ""):
            smtp.login(smtp_config['server']['username'], smtp_config['server']['password']) 
        smtp.send_message(msg)
        smtp.quit()
