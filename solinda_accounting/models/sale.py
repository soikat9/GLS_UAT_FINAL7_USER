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
        if self.tag_ids:
            name_tag = self.tag_ids.mapped('name')
            if any('Turn Key' in w for w in name_tag):
                res.update({
                'tags_ids': self.tag_ids.ids,
                'name' : self.env["ir.sequence"].next_by_code("account.move.sequence.turnkey")
                })
            elif any('BOO' in w for w in name_tag):
                res.update({
                'tags_ids': self.tag_ids.ids,
                'name' : self.env["ir.sequence"].next_by_code("account.move.sequence.boo")
                })
            elif any('OMS' in w for w in name_tag):
                res.update({
                'tags_ids': self.tag_ids.ids,
                'name' : self.env["ir.sequence"].next_by_code("account.move.sequence.oms")
                })
            elif any('Trading' in w for w in name_tag):
                res.update({
                'tags_ids': self.tag_ids.ids,
                'name' : self.env["ir.sequence"].next_by_code("account.move.sequence.trading")
                })
            else:
                res.update({
                'tags_ids': self.tag_ids.ids,
                })
        return res