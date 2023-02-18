# -*- coding: utf-8 -*-
# from odoo import http


# class SolImportFiel(http.Controller):
#     @http.route('/sol_import_fiel/sol_import_fiel', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sol_import_fiel/sol_import_fiel/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('sol_import_fiel.listing', {
#             'root': '/sol_import_fiel/sol_import_fiel',
#             'objects': http.request.env['sol_import_fiel.sol_import_fiel'].search([]),
#         })

#     @http.route('/sol_import_fiel/sol_import_fiel/objects/<model("sol_import_fiel.sol_import_fiel"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sol_import_fiel.object', {
#             'object': obj
#         })
