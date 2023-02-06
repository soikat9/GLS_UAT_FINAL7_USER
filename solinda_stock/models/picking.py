from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    return_reasons = fields.Text('Return Reason')

    def create_returns(self):
        res = super(StockReturnPicking,self).create_returns()  
        picking = self.env['stock.picking'].search([('id','=',res['res_id'])])
        picking.return_reasons = self.return_reasons
        return res


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _description = 'Stock Picking'
    
    ship_via = fields.Char(string='Ship Via')
    prepared = fields.Many2one('res.users', string='Prepared By')
    verified = fields.Many2one('res.users', string='Verified By')
    approved = fields.Many2one('res.users', string='Approved By')
    received = fields.Many2one('res.users', string='Received By')
    serial = fields.Char(string='PO Number')
    return_reasons = fields.Text('Return Reason')
    
    def button_validate(self):
        for i in self:
            if i.picking_type_id:
                for t in i.picking_type_id:
                    if t.code == 'internal' and not self.user_has_groups("solinda_stock.validate_internal_groupsol"):
                        raise ValidationError("You are not allowed to validate this document!")
                    elif t.code == 'outgoing' and not self.user_has_groups("solinda_stock.sales_marketing_groupsol"):
                        raise ValidationError("You are not allowed to validate this document!")
        return super(StockPicking,self).button_validate()  

    def _action_generate_backorder_wizard(self, show_transfers=False):
        view = self.env.ref('stock.view_backorder_confirmation')
        return {
            'name': _('Create Partial?'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'stock.backorder.confirmation',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': dict(self.env.context, default_show_transfers=show_transfers, default_pick_ids=[(4, p.id) for p in self]),
        }