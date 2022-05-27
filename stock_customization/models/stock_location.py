# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class Location(models.Model):
	_inherit = 'stock.location'

	condition_id = fields.Many2one("condition.stock", string="Condition", ondelete="restrict")
	status_id = fields.Many2one("status.stock", string="Status", ondelete="restrict")
	delivery_location = fields.Boolean(string="Is a helpdesk delivery location?", default=False)
	sim_location = fields.Boolean(string="Is a SIM location?", default=False)