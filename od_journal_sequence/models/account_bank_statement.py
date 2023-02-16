from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    name = fields.Char(string='Reference',
                       states={'open': [('readonly', False)]},
                       copy=False,
                       readonly=True,
                       compute="_compute_name",
                       store=True)
    
    @api.depends('move_line_ids.move_id.name')
    def _compute_name(self):
        for line in self.move_line_ids:
            ref = ''
            if line.move_id:
                name = line.move_id.mapped("name")
                for move in name:
                    ref += move
                self.name = ref

