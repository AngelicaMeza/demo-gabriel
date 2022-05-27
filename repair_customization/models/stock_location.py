# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class Location(models.Model):
	_inherit = "stock.location"
	
	repair_location = fields.Boolean('Is a Repair Location?', default=False, help='Check this box to allow using this location to put devices to repair.')