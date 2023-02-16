from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    name = fields.Char(string='Reference',
                       states={'open': [('readonly', False)]},
                       copy=False,
                       readonly=True,
                       related='move_id.name',
                       store=True)

