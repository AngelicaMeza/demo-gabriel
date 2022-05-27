# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class Users(models.Model):
	_inherit = "res.users"

	workcenter_user_ids = fields.One2many('mrp.workcenter.user.line', 'user_id', string='Workcenters', readonly=True)