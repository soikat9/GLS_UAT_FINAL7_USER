from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    name = fields.Char(string='Reference',
                       states={'open': [('readonly', False)]},
                       copy=False,
                       readonly=True,
                       store=True)
    
    @api.onchange('move_id')
    def _onchange_move_id_name(self):
        for statement in self:
            if statement.move_id:
                statement.name = statement.move_id.name
            else:
                statement.name = "/"

