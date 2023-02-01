from odoo import api, fields, models

class AccountAsset(models.Model):
    _inherit = 'account.asset'

    asset_code = fields.Char('Asset Code')