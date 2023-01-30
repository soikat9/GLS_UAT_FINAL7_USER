from odoo import models, fields, api

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    @api.depends('can_edit_wizard')
    def _compute_communication(self):
        # The communication can't be computed in '_compute_from_lines' because
        # it's a compute editable field and then, should be computed in a separated method.
        for wizard in self:
            if wizard.can_edit_wizard:
                # batches = wizard._get_batches()
                wizard.communication = False
            else:
                wizard.communication = False

    communication = fields.Char(string="Memo", store=True, readonly=False)
