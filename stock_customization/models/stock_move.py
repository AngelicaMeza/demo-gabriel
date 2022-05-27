# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class StockMove(models.Model):
	_inherit = 'stock.move'

	assembly_date = fields.Date(string="Assembly date", copy=False)
	assembly_place = fields.Many2one('res.country', string="Assembly place", copy=False)
	production_line = fields.Char(string="Production line", copy=False)
	product_type = fields.Selection(related='product_id.product_type')

	def confirm_detailed_operations(self):
		for rec in self.move_line_ids:
			if rec.lot_id:
				if self.assembly_date:
					rec.lot_id.assembly_date = self.assembly_date
				if self.assembly_place:
					rec.lot_id.assembly_place = self.assembly_place
				if self.production_line:
					rec.lot_id.production_line = self.production_line

	@api.onchange('picking_type_id')
	def _only_sim_key_products(self):
		"""
			When picking_type_id have is_sim_operation_move in True
			only you can select a Simcard product

			When picking_type_id have is_key_operation in True
			only you can select a Key product
		"""
		if self.picking_type_id and self.picking_type_id.is_sim_operation_move:
			return {'domain': {'product_id': [('product_type','=','3')]}}
		elif self.picking_type_id and self.picking_type_id.is_key_operation:
			return {'domain': {'product_id': [('product_type','=','5')]}}

	def _action_done(self, cancel_backorder=False):
		moves_todo = super(StockMove, self)._action_done(cancel_backorder)

		for rec in moves_todo:
			picking = rec.picking_id
			if picking.location_dest_id.usage == 'customer':
				if rec.move_line_ids.lot_id and rec.product_id.tracking == 'serial':
					rec.move_line_ids.lot_id.partner_id = picking.partner_id
					rec.move_line_ids.lot_id.affiliated = rec.move_line_ids.lot_id.partner_id.affiliated
					rec.move_line_ids.lot_id.negotiation_type_id = picking.sale_id.type_negotiation_id if picking.sale_id and rec.product_id.product_type in ['0', '1', '2'] else False

			#Cambia el estatus y condicion del lote por los valores de la ubicacion destino
			if picking.location_dest_id:
				if picking.location_dest_id.condition_id:
					rec.move_line_ids.lot_id.condition_id = picking.location_dest_id.condition_id
				if picking.location_dest_id.status_id:
					rec.move_line_ids.lot_id.status_id = picking.location_dest_id.status_id
				if picking.picking_type_id.code == 'outgoing':
					rec.move_line_ids.lot_id.move_id = rec

			try:
				rec.move_line_ids.lot_id.current_location = rec.move_line_ids.location_dest_id
				warehouse = rec.env['stock.warehouse'].search([('view_location_id', 'parent_of', rec.move_line_ids.location_dest_id.id)], limit=1)
				rec.move_line_ids.lot_id.warehouse_id = warehouse
				rec.move_line_ids.lot_id.in_warehouse_date = rec.date if warehouse else False
			except:
				continue

		return moves_todo

class StockMoveLine(models.Model):
	_inherit = 'stock.move.line'

	is_sim_operation = fields.Boolean(compute='_compute_is_sim_operation')
	sim_lot_id = fields.Many2one('stock.production.lot', string='SIM')
	condition_id = fields.Many2one(related='lot_id.condition_id', readonly=True)
	status_id = fields.Many2one(related='lot_id.status_id', readonly=True)

	@api.depends('picking_id.picking_type_id', 'product_id')
	def _compute_is_sim_operation(self):
		"""
			set is_sim_operation in True if product_id is a POS
			and a wireless network devices
		"""
		for move_line in self:
			if(
				move_line.picking_id.picking_type_id.is_sim_operation and\
				move_line.product_id.product_type in ['0','1'] and\
				move_line.product_id.tracking == 'serial' and\
				any(c.type_code == 1 for c in move_line.product_id.communication_id)
			):
				move_line.is_sim_operation = True
			else:
				move_line.is_sim_operation = False
	
	def validate_sim_operations(self):
		for line in self.filtered(lambda l: l.is_sim_operation and l.sim_lot_id):
			line.lot_id.write({
				'sim_card': line.sim_lot_id.id
			})

	@api.onchange('picking_id')
	def _only_sim_key_products(self):
		"""
			When picking_type_id have is_sim_operation_move in True
			only you can select a Simcard product

			When picking_type_id have is_key_operation in True
			only you can select a Key product
		"""
		if self.picking_id.picking_type_id and self.picking_id.picking_type_id.is_sim_operation_move:
			return {'domain': {'product_id': [('product_type','=','3')]}}
		elif self.picking_id.picking_type_id and self.picking_id.picking_type_id.is_key_operation:
			return {'domain': {'product_id': [('product_type','=','5')]}}
			
class StockRule(models.Model):
	_inherit = 'stock.rule'

	def _push_prepare_move_copy_values(self, move_to_copy, new_date):
		res = super()._push_prepare_move_copy_values(move_to_copy, new_date)
		res['partner_id'] = move_to_copy.picking_id.partner_id.id
		return res
