from odoo import models, fields, api

class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    # ref = fields.Char(string='Bill Reference', related='expense_line_ids.reference')
    # start_date = fields.Date(string='Plan Date')
    # end_date = fields.Date(string='End Date')