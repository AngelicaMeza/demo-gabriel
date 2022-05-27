# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	request_mrp_order_id = fields.Many2one('mrp.production')

class MrpProduction(models.Model):
	_inherit = 'mrp.production'

	request_keys_ids = fields.One2many('stock.picking', 'request_mrp_order_id', string='Solicitud de llaves')
	application_version = fields.Many2one('application.versions', string="Application version", ondelete="restrict")
	product_brand = fields.Many2one(related='product_id.brand_id')
	product_type = fields.Selection(related="product_id.product_type")
	key_version = fields.Many2one('product.product', string="Key version")

	def action_request_keys(self):
		self.ensure_one()
		ctx = self._context.copy()
		ctx['default_mrp_order_ids'] = [(6, 0, self.ids)]
		ctx['default_warehouse_id'] = self.picking_type_id.warehouse_id.id
		ctx['default_picking_type_id'] = self.env['stock.picking.type'].search([('warehouse_id', '=', self.picking_type_id.warehouse_id.id), ('is_key_operation', '=', True)], limit=1).id
		if self.key_version:
			wizard_lines = []
			wizard_lines.append((0, 0, {
						'product_id': self.key_version.id,
						'quantity': 1
					}))
			ctx['default_product_ids'] = wizard_lines
		return {
			'type': 'ir.actions.act_window',
			'name': 'Solicitud de llaves',
			'res_model': 'request.keys',
			'view_mode': 'form',
			'context': ctx,
			'target': 'new',
		}
	
	@api.depends('procurement_group_id', 'request_keys_ids')
	def _compute_picking_ids(self):
		super()._compute_picking_ids()
		for mrp in self:
			mrp.picking_ids += mrp.request_keys_ids
			mrp.delivery_count = len(mrp.picking_ids)

	def button_mark_done(self):
		self.ensure_one()
		if self.application_version and self.key_version:
			for product in self.finished_move_line_ids:
				if product.lot_id:
					product.lot_id.application_version = self.application_version
					product.lot_id.key_version = self.key_version
		else:
			raise ValidationError(_("""Asegurate de colocar una versión de aplicativo y llave antes de marcar como hecho."""))
		return super(MrpProduction, self).button_mark_done()