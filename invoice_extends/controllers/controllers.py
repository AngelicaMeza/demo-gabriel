# -*- coding: utf-8 -*-
# from odoo import http


# class InvoiceExtends(http.Controller):
#     @http.route('/invoice_extends/invoice_extends/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/invoice_extends/invoice_extends/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('invoice_extends.listing', {
#             'root': '/invoice_extends/invoice_extends',
#             'objects': http.request.env['invoice_extends.invoice_extends'].search([]),
#         })

#     @http.route('/invoice_extends/invoice_extends/objects/<model("invoice_extends.invoice_extends"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('invoice_extends.object', {
#             'object': obj
#         })
