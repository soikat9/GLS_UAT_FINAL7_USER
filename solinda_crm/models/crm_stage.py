from odoo import _, api, fields, models

class CrmStage(models.Model):
    _inherit = 'crm.stage'

    percent_from = fields.Float(string='From')
    percent_to = fields.Float(string='To')

    percentage_range = fields.Char(compute='_compute_percentage_range', string='Probability Range')
    
    @api.depends('percent_from','percent_to')
    def _compute_percentage_range(self):
        for i in self:
            i.percentage_range = "%s - %s" % (i.percent_from,i.percent_to)
        