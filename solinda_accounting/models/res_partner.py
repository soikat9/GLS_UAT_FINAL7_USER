from odoo import fields, api, models

class ResPartner(models.Model):

    _inherit = 'res.partner'

    l10n_ar_vat = fields.Char(
        compute='_compute_l10n_ar_vat', string="Tax ID", help='Computed field that returns VAT or nothing if this one'
        ' is not set for the partner')