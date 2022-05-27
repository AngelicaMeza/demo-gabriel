# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"
    _description = "Sales Analysis Report"

    kind_attention = fields.Selection([('1', 'Tradicional'), ('2', 'Evento'), ('3', 'VIP')], string="Tipo de atención")
    event_name_id = fields.Many2one(comodel_name='event.name', string="Nombre del evento")
    approved_regional_management_user = fields.Many2one(comodel_name ='res.users', string='Aprobado por')
    finance_approved_user = fields.Many2one(comodel_name ='res.users', string='Aprobado por')
    sales_executive = fields.Many2one(comodel_name='res.users',string="Ejecutivo vendedor")
    affiliated = fields.Char(string="Numero de afiliación")
    denomination = fields.Char(string="Denominación comercial")
    cluster_id = fields.Many2one(comodel_name ='segmentation.cluster', string='Cluster')
    name_owner =fields.Char(string ="Nombre y Apellido del Propietario")
    region_id = fields.Many2one('crm.region',string='Región')
    regional_manager = fields.Many2one(comodel_name='res.users', string="Gerente Regional")
    parent_id = fields.Many2one('res.partner', string='Empresa relacionada')
    product_type = fields.Selection([
        ('1', 'POS'),
        ('2', 'Accesorios'),
        ('3', 'POS y Accesorios')
    ], string="Tipo de Producto")
    type_point_sale_id = fields.Many2one(comodel_name='crm.point.sale', string="Tipo de comunicación")
    company_pos_id = fields.Many2one(comodel_name='crm.company.pos', string="Operadora Telefónica")
    type_negotiation_id = fields.Many2one(comodel_name='crm.negotiation', string="Tipo de negociación")
    origin_id = fields.Many2one(comodel_name='crm.origin', string="Origen")

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        new_fields_order = {
            'kind_attention': ", s.kind_attention as kind_attention",
            'event_name_id': ", s.event_name_id as event_name_id",
            'approved_regional_management_user': ", s.approved_regional_management_user as approved_regional_management_user",
            'finance_approved_user': ", s.finance_approved_user as finance_approved_user",
            'sales_executive': ", s.sales_executive as sales_executive",
            'affiliated': ", s.affiliated as affiliated",
            'denomination': ", s.denomination as denomination",
            'cluster_id': ", s.cluster_id as cluster_id",
            'name_owner': ", s.name_owner as name_owner",
            'region_id': ", s.region_id as region_id",
            'regional_manager': ", s.regional_manager as regional_manager",
            'parent_id': ", s.parent_id as parent_id",
            'product_type': ", s.product_type as product_type",
            'type_point_sale_id': ", s.type_point_sale_id as type_point_sale_id",
            'company_pos_id': ", s.company_pos_id as company_pos_id",
            'origin_id': ", s.origin_id as origin_id",
            'type_negotiation_id': ", s.type_negotiation_id as type_negotiation_id",
        }
        fields.update(new_fields_order)
        for key in new_fields_order:
            groupby += ', s.%s' % key 
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)