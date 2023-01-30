from odoo import _, api, fields, models

class ProductProduct(models.Model):
    _inherit = 'product.product'

    part_no = fields.Char('Part Number')
    chemical_catridge_usage = fields.Float('Chemical Catridge Usage')
