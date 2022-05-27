# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class WarehouseUserLine(models.Model):
	_name = "stock.warehouse.user.line"
	_description = "Warehouse User Line"

	def _default_domain_user_id(self):
		return [('groups_id', 'in', self.env.ref('stock_access_rights.group_stock_assign').id)]

	warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
	user_id = fields.Many2one('res.users', string='User', domain=lambda self: self._default_domain_user_id(), required=True)
	picking_type_ids = fields.Many2many('stock.picking.type', string='Operation Types')


class Warehouse(models.Model):
	_inherit = "stock.warehouse"

	user_line_ids = fields.One2many('stock.warehouse.user.line', 'warehouse_id', string='Users')

	def write(self, values):
		self.clear_caches()
		return super(Warehouse, self).write(values)