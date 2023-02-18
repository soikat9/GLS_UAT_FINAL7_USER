# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class sol_import_fiel(models.Model):
#     _name = 'sol_import_fiel.sol_import_fiel'
#     _description = 'sol_import_fiel.sol_import_fiel'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
