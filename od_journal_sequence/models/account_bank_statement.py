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
    
    @api.depends('line_ids.move_id')
    def _compute_name(self):
        for line in self.line_ids:
            if line.move_id:
                name = line.move_id.mapped("name")
                self.name = name

