from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    # ref = fields.Char(string='Bill Reference', related='expense_line_ids.reference')
    # start_date = fields.Date(string='Plan Date')
    # end_date = fields.Date(string='End Date')
    # def _compute_attachment_number(self):
    #     for sheet in self:
    #         sheet.attachment_number = sum(sheet.expense_line_ids.mapped('attachment_number'))
    #         if sheet.attachment_number == 0:
    #             raise ValidationError("Attachment Must be Fill")