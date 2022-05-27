# -*- coding: utf-8 -*-
# from odoo import http


# class ../extra-addons/nativa/crmPartnerInherit(http.Controller):
#     @http.route('/../extra-addons/nativa/crm_partner_inherit/../extra-addons/nativa/crm_partner_inherit/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/../extra-addons/nativa/crm_partner_inherit/../extra-addons/nativa/crm_partner_inherit/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('../extra-addons/nativa/crm_partner_inherit.listing', {
#             'root': '/../extra-addons/nativa/crm_partner_inherit/../extra-addons/nativa/crm_partner_inherit',
#             'objects': http.request.env['../extra-addons/nativa/crm_partner_inherit.../extra-addons/nativa/crm_partner_inherit'].search([]),
#         })

#     @http.route('/../extra-addons/nativa/crm_partner_inherit/../extra-addons/nativa/crm_partner_inherit/objects/<model("../extra-addons/nativa/crm_partner_inherit.../extra-addons/nativa/crm_partner_inherit"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('../extra-addons/nativa/crm_partner_inherit.object', {
#             'object': obj
#         })
