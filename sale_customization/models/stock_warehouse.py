# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    sale_stock_location = fields.Many2one('stock.location', 'Stock para venta', help="Ubicación de origen para la consulta de disponibilidad en venta")
    rental_stock_location= fields.Many2one('stock.location', 'Stock para alquiler', help="Ubicación de origen para la consulta de disponibilidad en alquiler")