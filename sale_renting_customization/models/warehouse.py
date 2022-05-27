# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    location_for_rental = fields.Many2one('stock.location')
    rental_location= fields.Many2one('stock.location')