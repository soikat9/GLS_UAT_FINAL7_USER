# -*- coding: utf-8 -*-
# from odoo import http


# class PurchaseAdvancePaymentTax(http.Controller):
#     @http.route('/purchase_advance_payment_tax/purchase_advance_payment_tax', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/purchase_advance_payment_tax/purchase_advance_payment_tax/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('purchase_advance_payment_tax.listing', {
#             'root': '/purchase_advance_payment_tax/purchase_advance_payment_tax',
#             'objects': http.request.env['purchase_advance_payment_tax.purchase_advance_payment_tax'].search([]),
#         })

#     @http.route('/purchase_advance_payment_tax/purchase_advance_payment_tax/objects/<model("purchase_advance_payment_tax.purchase_advance_payment_tax"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('purchase_advance_payment_tax.object', {
#             'object': obj
#         })
