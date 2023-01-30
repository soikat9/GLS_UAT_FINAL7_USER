from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountVoucherWizardPurchase(models.TransientModel):
    _inherit = "account.voucher.wizard.purchase"

    tax_ids = fields.Many2many(comodel_name='account.tax', string='Tax', domain=[('type_tax_use', '=', 'purchase')])
    total_amount_advance = fields.Monetary(string='Total Amount Advance', readonly=True, currency_field='journal_currency_id')

    @api.onchange('tax_ids', 'amount_advance')
    def onchange_total_amount_advance(self):
        for rec in self:
            amount_with_tax = self.tax_ids.compute_all(self.amount_advance, self.journal_currency_id)
            rec.write({'total_amount_advance':  amount_with_tax.get('total_included', rec.amount_advance)})
    
    def _prepare_payment_vals(self, purchase):
        res = super(AccountVoucherWizardPurchase, self)._prepare_payment_vals(purchase)
        amount_with_tax = self.tax_ids.compute_all(self.amount_advance, self.journal_currency_id)
        res['amount'] = amount_with_tax.get('total_included', res['amount'])
        return res
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        purchase_ids = self.env.context.get("active_ids", [])
        if not purchase_ids:
            return res
        purchase_id = fields.first(purchase_ids)
        purchase = self.env["purchase.order"].browse(purchase_id)
        if "tax_ids" in fields_list:
            res.update(
                {
                    "tax_ids": purchase.order_line[0].taxes_id.ids if len(purchase.order_line) > 1 else purchase.order_line.taxes_id.ids,
                }
            )

        return res