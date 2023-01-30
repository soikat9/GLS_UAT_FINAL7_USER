from odoo import _, api, fields, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _description = 'Stock Picking'
    
    shutdown_id = fields.Many2one('shutdown.system', string='Shutdown')
    job_order_id = fields.Many2one('job.order.request', string='Job Order') 
    maintenance_id = fields.Many2one('maintenance.request', string='Maintenance') 


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.onchange('company_id','location_id','picking_type_id')
    def _onchange_productby_equipment(self):
        for i in self:
            if i.picking_id.maintenance_id:
                return {'domain': {'product_id': [('id', 'in', i.picking_id.maintenance_id.equipment_id.spare_part_ids.mapped('product_id').ids)]}}
