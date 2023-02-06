from odoo import _, api, fields, models

class MailActivityType(models.Model):
    _inherit = 'mail.activity.type'

    
    progress = fields.Float('Progress')
    cspr = fields.Boolean('Contract Signed / PO Receive')