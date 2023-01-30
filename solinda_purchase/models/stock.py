from odoo import _, api, fields, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    

    def button_validate(self):
        for i in self:
            if i.purchase_id:
                i.purchase_id.state = 'done'
        return super(StockPicking,self).button_validate()  

    
