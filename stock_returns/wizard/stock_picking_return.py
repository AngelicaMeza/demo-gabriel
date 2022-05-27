# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round, float_is_zero, float_compare
from itertools import groupby
from operator import itemgetter
from odoo.addons.stock_account.wizard.stock_picking_return import StockReturnPicking

def _create_returns(self):
	new_picking_id, pick_type_id = super(StockReturnPicking, self)._create_returns()
	new_picking = self.env['stock.picking'].browse([new_picking_id])
	for move in new_picking.move_lines:
		for return_picking_line in self.product_return_moves.filtered(lambda r: r.move_id == move.origin_returned_move_id):
			if return_picking_line and return_picking_line.to_refund:
				move.to_refund = True
				break
	return new_picking_id, pick_type_id

StockReturnPicking._create_returns = _create_returns

class ReturnPickingLine(models.TransientModel):
	_inherit = "stock.return.picking.line"

	tracking = fields.Selection(related='product_id.tracking')
	lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial Number')

	@api.onchange('product_id')
	def _set_move_id_product(self):
		if self.product_id and self.product_id.tracking == 'none':
			move = self.wizard_id.picking_id.move_lines.filtered(lambda m: m.product_id == self.product_id)
			if move and move.id in self.wizard_id.product_return_moves.move_id.ids:
				raise UserError(_("This line already exits !!!"))
	
	@api.onchange('lot_id')
	def _set_move_id_by_lot(self):
		if self.lot_id:
			move_line_id = self.wizard_id.picking_id.move_line_ids.filtered(lambda m: m.lot_id == self.lot_id)
			self.move_id = move_line_id.move_id.id

class ReturnPicking(models.TransientModel):
	_inherit = "stock.return.picking"

	product_domain = fields.Many2many('product.product', string='Product domain')
	lot_domain = fields.Many2many('stock.production.lot', string='Lot domain')

	@api.onchange('product_return_moves')
	def _set_product_lot_domain(self):
		if self.product_return_moves:
			picking_lots = set(self.picking_id.move_line_ids.mapped('lot_id').ids)
			wizard_lots = set(self.product_return_moves.mapped('lot_id').ids)
			self.lot_domain = list(picking_lots - wizard_lots) or False
		else:
			self.lot_domain = self.picking_id.move_line_ids.mapped('lot_id').ids

	@api.onchange('picking_id')
	def _onchange_picking_id(self):
		move_dest_exists = False
		product_return_moves = [(5,)]
		if self.picking_id and self.picking_id.state != 'done':
			raise UserError(_("You may only return Done pickings."))
		# In case we want to set specific default values (e.g. 'to_refund'), we must fetch the
		# default values for creation.
		line_fields = [f for f in self.env['stock.return.picking.line']._fields.keys()]
		product_return_moves_data_tmpl = self.env['stock.return.picking.line'].default_get(line_fields)

		################################################################################################
		self.product_domain = self.picking_id.move_lines.mapped('product_id').ids
		################################################################################################
		products = False
		if self.picking_id.quality_alert_ids:
			products = self.picking_id.quality_alert_ids.mapped('product_id')
		################################################################################################

		for move in self.picking_id.move_lines:
			if move.state == 'cancel':
				continue
			if move.scrapped:
				continue
			if move.move_dest_ids:
				move_dest_exists = True
			
			################################################################################################
			if products and move.product_id not in products:
				continue
			################################################################################################
			if move.product_id.tracking == 'none':
				product_return_moves_data = dict(product_return_moves_data_tmpl)
				product_return_moves_data.update(self._prepare_stock_return_picking_line_vals_from_move(move))
				product_return_moves.append((0, 0, product_return_moves_data))
			
			else:
				if products:
					move_line_ids = move.move_line_ids.filtered(lambda x: x.lot_id in self.picking_id.quality_alert_ids.mapped('lot_id'))
				else:
					move_line_ids = move.move_line_ids
				for move_line in move_line_ids:
					if products and move_line.tracking == 'lot':
						quantity = 0
					else:
						quantity = move_line.qty_done
					product_return_moves_data = dict(product_return_moves_data_tmpl)
					product_return_moves_data.update({
						'product_id': move_line.product_id.id,
						'lot_id': move_line.lot_id.id,
						'quantity': quantity,
						'move_id': move_line.move_id.id,
						'uom_id': move_line.product_id.uom_id.id,
					})
					product_return_moves.append((0, 0, product_return_moves_data))
			#################################################################################################
		
		if self.picking_id and not product_return_moves:
			raise UserError(_("No products to return (only lines in Done state and not fully returned yet can be returned)."))
		if self.picking_id:
			self.product_return_moves = product_return_moves
			self.move_dest_exists = move_dest_exists
			self.parent_location_id = self.picking_id.picking_type_id.warehouse_id and self.picking_id.picking_type_id.warehouse_id.view_location_id.id or self.picking_id.location_id.location_id.id
			self.original_location_id = self.picking_id.location_id.id
			location_id = self.picking_id.location_id.id
			if self.picking_id.picking_type_id.return_picking_type_id.default_location_dest_id.return_location:
				location_id = self.picking_id.picking_type_id.return_picking_type_id.default_location_dest_id.id
			self.location_id = location_id

	@api.model
	def _prepare_stock_return_picking_line_vals_from_move(self, stock_move):
		quantity = stock_move.product_qty
		for move in stock_move.move_dest_ids:
			if move.origin_returned_move_id and move.origin_returned_move_id != stock_move:
				continue
			if move.state in ('partially_available', 'assigned'):
				quantity -= sum(move.move_line_ids.mapped('product_qty'))
			elif move.state in ('done'):
				quantity -= move.product_qty
		#################################################################################
		if self.picking_id.quality_alert_ids:
			quantity = 0
		else:
			quantity = float_round(quantity, precision_rounding=stock_move.product_uom.rounding)
		#################################################################################
		return {
			'product_id': stock_move.product_id.id,
			'quantity': quantity,
			'move_id': stock_move.id,
			'uom_id': stock_move.product_id.uom_id.id,
		}
	
	def _create_returns(self):
		if len(self.product_return_moves.filtered(lambda l: l.quantity < 1)):
			raise UserError(_("""There are line with cero quantity."""))
		
		for return_move in self.product_return_moves.mapped('move_id'):
			return_move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._do_unreserve()

		# create new picking for returned products
		picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id
		new_picking = self.picking_id.copy({
			'move_lines': [],
			'picking_type_id': picking_type_id,
			'state': 'draft',
			'origin': _("Return of %s") % self.picking_id.name,
			'location_id': self.picking_id.location_dest_id.id,
			'location_dest_id': self.location_id.id})
		new_picking.message_post_with_view('mail.message_origin_link',
			values={'self': new_picking, 'origin': self.picking_id},
			subtype_id=self.env.ref('mail.mt_note').id)
		returned_lines = 0
		for return_line in self.product_return_moves:
			if not return_line.move_id:
				raise UserError(_("You have manually created product lines, please delete them to proceed."))
			# TODO sle: float_is_zero?
			if return_line.quantity:
				returned_lines += 1
				vals = self._prepare_move_default_values(return_line, new_picking)
				r = return_line.move_id.copy(vals)
				vals = {}

				# +--------------------------------------------------------------------------------------------------------+
				# |       picking_pick     <--Move Orig--    picking_pack     --Move Dest-->   picking_ship
				# |              | returned_move_ids              ↑                                  | returned_move_ids
				# |              ↓                                | return_line.move_id              ↓
				# |       return pick(Add as dest)          return toLink                    return ship(Add as orig)
				# +--------------------------------------------------------------------------------------------------------+
				move_orig_to_link = return_line.move_id.move_dest_ids.mapped('returned_move_ids')
				# link to original move
				move_orig_to_link |= return_line.move_id
				# link to siblings of original move, if any
				move_orig_to_link |= return_line.move_id\
					.mapped('move_dest_ids').filtered(lambda m: m.state not in ('cancel'))\
					.mapped('move_orig_ids').filtered(lambda m: m.state not in ('cancel'))
				move_dest_to_link = return_line.move_id.move_orig_ids.mapped('returned_move_ids')
				# link to children of originally returned moves, if any. Note that the use of
				# 'return_line.move_id.move_orig_ids.returned_move_ids.move_orig_ids.move_dest_ids'
				# instead of 'return_line.move_id.move_orig_ids.move_dest_ids' prevents linking a
				# return directly to the destination moves of its parents. However, the return of
				# the return will be linked to the destination moves.
				move_dest_to_link |= return_line.move_id.move_orig_ids.mapped('returned_move_ids')\
					.mapped('move_orig_ids').filtered(lambda m: m.state not in ('cancel'))\
					.mapped('move_dest_ids').filtered(lambda m: m.state not in ('cancel'))
				vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link]
				vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
				r.write(vals)
		if not returned_lines:
			raise UserError(_("Please specify at least one non-zero quantity."))

		new_picking.action_confirm()
		new_picking.action_assign_returns(self)
		return new_picking.id, picking_type_id

		# ########################################################################################
		# if len(self.product_return_moves.filtered(lambda l: l.quantity < 1)):
		# 	raise UserError(_("""There are line with cero quantity."""))
		# ########################################################################################

		# new_picking, picking_type_id = super(ReturnPicking, self)._create_returns()

		# ###################################################################################
		# picking = self.env['stock.picking'].browse([new_picking])
		# for move in picking.move_lines:
		# 	return_moves = self.product_return_moves.filtered(lambda p: p.move_id == move.origin_returned_move_id)
		# 	if any([r_move.lot_id not in move.move_line_ids.lot_id for r_move in return_moves]):
		# 		move_lines_to_unlink = move.move_line_ids
		# 		for move_line, return_move in zip(move.move_line_ids, return_moves):
		# 			need = move.product_qty - sum(move.move_line_ids.mapped('product_qty'))
		# 			rounding = move_line.product_id.uom_id.rounding
		# 			available_quantity = self.env['stock.quant']._get_available_quantity(
		# 				move_line.product_id, move_line.location_id, lot_id=return_move.lot_id, package_id=move_line.package_id, owner_id=move_line.owner_id, strict=True)
		# 			if float_is_zero(available_quantity, precision_rounding=rounding):
		# 				continue
		# 			taken_quantity = move._update_reserved_quantity(need, min(return_move.quantity, available_quantity), move_line.location_id, return_move.lot_id, move_line.package_id, move_line.owner_id)
		# 	# move.move_line_ids.filtered(lambda m: m.id in move_lines_to_unlink.ids).unlink()
		# ##########################################################################################

		# return new_picking, picking_type_id