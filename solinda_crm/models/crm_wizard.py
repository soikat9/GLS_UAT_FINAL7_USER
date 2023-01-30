from odoo import api, fields, models

class Lead2OpportunityPartner(models.TransientModel):
  _inherit = 'crm.lead2opportunity.partner'

  name = fields.Selection([
    ('convert', 'Convert to opportunity'),
    ('merge', 'Merge with existing opportunities')
  ], 'Conversion Action', compute='_compute_name', readonly=False, store=True, compute_sudo=False, default='convert')