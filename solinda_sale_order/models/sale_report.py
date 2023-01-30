from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.osv.expression import expression


class SaleReport(models.Model):
    _inherit = 'sale.report'

    tag_string = fields.Char('Tags')

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['tag_string'] = ', s.tag_string as tag_string'
        groupby += ', s.tag_string'

        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
