# -*- coding: utf-8 -*-
# from odoo import http


# class ../extra-addons/nativa/crmLeadForm(http.Controller):
#     @http.route('/../extra-addons/nativa/crm_lead_form/../extra-addons/nativa/crm_lead_form/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/../extra-addons/nativa/crm_lead_form/../extra-addons/nativa/crm_lead_form/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('../extra-addons/nativa/crm_lead_form.listing', {
#             'root': '/../extra-addons/nativa/crm_lead_form/../extra-addons/nativa/crm_lead_form',
#             'objects': http.request.env['../extra-addons/nativa/crm_lead_form.../extra-addons/nativa/crm_lead_form'].search([]),
#         })

#     @http.route('/../extra-addons/nativa/crm_lead_form/../extra-addons/nativa/crm_lead_form/objects/<model("../extra-addons/nativa/crm_lead_form.../extra-addons/nativa/crm_lead_form"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('../extra-addons/nativa/crm_lead_form.object', {
#             'object': obj
#         })
