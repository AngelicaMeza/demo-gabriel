# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_compare

##########################################################################################
from odoo.addons.sale_stock_renting.models.sale_rental import RentalOrderLine as Rental
from odoo.addons.sale_stock.models.sale_order import SaleOrderLine
##########################################################################################

def _compute_qty_delivered_method(self):
	"""Override this method to continue its normal flow"""
	super(Rental, self)._compute_qty_delivered_method()

@api.depends('move_ids.state', 'move_ids.scrapped', 'move_ids.product_uom_qty', 'move_ids.product_uom')
def _compute_qty_delivered(self):
	"""
	Override this method to identify when a stock move comes from a return
	and add the quantity of products returned to its respective rental order line
	"""
	super(SaleOrderLine, self)._compute_qty_delivered()

	for line in self:  # TODO: maybe one day, this should be done in SQL for performance sake
		if line.qty_delivered_method == 'stock_move':
			qty = 0.0
			outgoing_moves, incoming_moves = line._get_outgoing_incoming_moves()
			for move in outgoing_moves:
				if move.state != 'done':
					continue
				qty += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom, rounding_method='HALF-UP')
			for move in incoming_moves:
				#don't decrease quantity if is_rental line
				if move.state != 'done' or line.is_rental:
					continue
				qty -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom, rounding_method='HALF-UP')
			line.qty_delivered = qty

############################################################################################
#	Replace methods
############################################################################################
Rental._compute_qty_delivered_method = _compute_qty_delivered_method
SaleOrderLine._compute_qty_delivered = _compute_qty_delivered
############################################################################################

class RentalOrderLine(models.Model):
	_inherit = "sale.order.line"

	qty_returned = fields.Float(compute='_compute_qty_returned', store=True)
	reserved_lot_ids = fields.Many2many(compute='_compute_planned_lot_ids', store=True)
	pickedup_lot_ids = fields.Many2many(compute='_compute_planned_lot_ids', store=True)
	# returned_lot_ids = fields.Many2many(compute='_compute_qty_returned', store=True)

	def _action_launch_stock_rule(self, previous_product_uom_qty=False):
		"""Available stock picking for rental order lines."""
		super(RentalOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)

		precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
		procurements = []
		############################## ONLY IS_RENTAL LINES ################################## 
		for line in self.filtered(lambda sol: sol.is_rental):
			if line.state != 'sale' or not line.product_id.type in ('consu','product'):
				continue
			qty = line._get_qty_procurement(previous_product_uom_qty)
			if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
				continue

			group_id = line._get_procurement_group()
			if not group_id:
				group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
				line.order_id.procurement_group_id = group_id
			else:
				# In case the procurement group is already created and the order was
				# cancelled, we need to update certain values of the group.
				updated_vals = {}
				if group_id.partner_id != line.order_id.partner_shipping_id:
					updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
				if group_id.move_type != line.order_id.picking_policy:
					updated_vals.update({'move_type': line.order_id.picking_policy})
				if updated_vals:
					group_id.write(updated_vals)

			values = line._prepare_procurement_values(group_id=group_id)
			product_qty = line.product_uom_qty - qty

			line_uom = line.product_uom
			quant_uom = line.product_id.uom_id
			product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
			################## TAKE THE RULE FOR RENTAL LOCATION #################
			procurements.append(self.env['procurement.group'].Procurement(
				line.product_id, product_qty, procurement_uom,
				line.order_id.warehouse_id.rental_location_id,
				line.name, line.order_id.name, line.order_id.company_id, values))
		if procurements:
			self.env['procurement.group'].run(procurements)
		return True

	def _get_outgoing_incoming_moves(self):
		outgoing_moves = self.env['stock.move']
		incoming_moves = self.env['stock.move']

		for move in self.move_ids.filtered(lambda r: r.state != 'cancel' and not r.scrapped and self.product_id == r.product_id):
			#################### ADD OUTOING_MOVE WHEN IS A RENTAL_LOCATION ########################
			if move.location_dest_id.usage == "customer" or move.location_dest_id.rental_location:
				if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
					outgoing_moves |= move
			elif move.location_dest_id.usage != "customer" and move.to_refund:
				incoming_moves |= move

		return outgoing_moves, incoming_moves

	@api.depends('move_ids.state', 'move_ids.scrapped', 'move_ids.product_uom_qty', 'move_ids.product_uom')
	def _compute_qty_returned(self):
		"""Compute the quantity returned in return pickings"""
		for line in self:
			qty_returned = 0.0
			if line.qty_delivered_method == 'stock_move' and line.is_rental:
				outgoing_moves, incoming_moves = line._get_outgoing_incoming_moves()
				for move in incoming_moves:
					if move.state != 'done':
						continue
					qty_returned += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom, rounding_method='HALF-UP')
			line.qty_returned = qty_returned

	@api.depends('move_ids.move_line_ids', 'move_ids.reserved_availability', 'move_ids.quantity_done')
	def _compute_planned_lot_ids(self):
		for line in self:

			if not line.reserved_lot_ids:
				line.reserved_lot_ids = []
			if not line.pickedup_lot_ids:
				line.pickedup_lot_ids = []


			if line.is_rental:

				reserved_lot_ids = []
				pickedup_lot_ids = []
				outgoing_moves, incoming_moves = line._get_outgoing_incoming_moves()
				
				for move_line in outgoing_moves.move_line_ids:
					if move_line.state == 'assigned' and move_line.product_uom_qty > 0 and move_line.lot_id:
						reserved_lot_ids.append(move_line.lot_id.id)
					elif move_line.state == 'done' and move_line.qty_done > 0 and move_line.lot_id:
						pickedup_lot_ids.append(move_line.lot_id.id)

				line.reserved_lot_ids = [(6, 0, reserved_lot_ids)]
				line.pickedup_lot_ids = [(6, 0, pickedup_lot_ids)]