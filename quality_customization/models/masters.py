# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class CheckPoint(models.Model):
	_name = "check.point"
	_description = "check point"
	_order = "sequence"

	sequence = fields.Integer()
	name = fields.Char()
	active = fields.Boolean('Active', default=True)

class CheckList(models.Model):
	_name = "check.list"
	_description = "check list"

	name = fields.Char()
	check_points = fields.Many2many('check.point', 'point_list', 'list', 'points', ondelete="restrict")
	active = fields.Boolean('Active', default=True)