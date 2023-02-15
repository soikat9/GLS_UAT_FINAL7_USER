from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, sequence=False):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res.update({
            'qty_delivered_account': self.qty_delivered,
            'qty_ordered_account' : self.product_uom_qty
            })
        return res

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res.update({
        'tags_ids': self.tag_ids.ids,
        'journal_id': None
        })
        return res