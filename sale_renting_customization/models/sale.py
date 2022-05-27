# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class RentalOrderLine(models.Model):
	_inherit = "sale.order.line"

	@api.model
	def write(self, vals):
		if not any(key in vals for key in ['qty_delivered', 'pickedup_lot_ids', 'qty_returned', 'returned_lot_ids']):
			# If nothing to catch for rental: usual write behavior
			return super(models.Model, self).write(vals)

		# TODO add context for disabling stock moves in write ?
		old_vals = dict()
		movable_confirmed_rental_lines = self.filtered(lambda sol: sol.is_rental and sol.state in ['sale', 'done'] and sol.product_id.type in ["product", "consu"])
		for sol in movable_confirmed_rental_lines:
			old_vals[sol.id] = (sol.pickedup_lot_ids, sol.returned_lot_ids) if sol.product_id.tracking == 'serial' else (sol.qty_delivered, sol.qty_returned)
			if vals.get('pickedup_lot_ids', False) and vals['pickedup_lot_ids'][0][0] == 6:
				pickedup_lot_ids = vals['pickedup_lot_ids'][0][2]
				if sol.product_uom_qty == len(pickedup_lot_ids) and pickedup_lot_ids != sol.reserved_lot_ids.ids:
					""" When setting the pickedup_lots:
					If the total reserved quantity is picked_up we need to unreserve
					the reserved_lots not picked to ensure the consistency of rental reservations.
					NOTE : This is only guaranteed for generic 6, _, _ orm magic commands.
					"""
					vals['reserved_lot_ids'] = vals['pickedup_lot_ids']

		res = super(models.Model, self).write(vals)
		if not movable_confirmed_rental_lines:
			return res

		# movable_confirmed_rental_lines.mapped('company_id').filtered(lambda company: not company.rental_loc_id)._create_rental_location()
			# to undo stock moves partially: what if location has changed? :x
			# can we ascertain the warehouse_id.lot_stock_id of a sale.order doesn't change???

		for sol in movable_confirmed_rental_lines:
			if sol.order_id.warehouse_id.rental_location:
				rented_location = sol.order_id.warehouse_id.rental_location
			else:
				raise ValidationError(_("The warehouse does not have a rental location"))
			if sol.order_id.warehouse_id.location_for_rental:
				stock_location = sol.order_id.warehouse_id.location_for_rental
			else:
				raise ValidationError(_("The warehouse does not have a location for rent"))
			if sol.product_id.tracking == 'serial' and (vals.get('pickedup_lot_ids', False) or vals.get('returned_lot_ids', False)):
				# for product tracked by serial numbers: move the lots
				if vals.get('pickedup_lot_ids', False):
					pickedup_lots = sol.pickedup_lot_ids - old_vals[sol.id][0]
					removed_pickedup_lots = old_vals[sol.id][0] - sol.pickedup_lot_ids
					sol._move_serials(pickedup_lots, stock_location, rented_location)
					sol._return_serials(removed_pickedup_lots, rented_location, stock_location)
				if vals.get('returned_lot_ids', False):
					returned_lots = sol.returned_lot_ids - old_vals[sol.id][1]
					removed_returned_lots = old_vals[sol.id][1] - sol.returned_lot_ids
					sol._move_serials(returned_lots, rented_location, stock_location)
					sol._return_serials(removed_returned_lots, stock_location, rented_location)
			elif sol.product_id.tracking != 'serial' and (vals.get('qty_delivered', False) or vals.get('qty_returned', False)):
				# for products not tracked : move quantities
				qty_delivered_change = sol.qty_delivered - old_vals[sol.id][0]
				qty_returned_change = sol.qty_returned - old_vals[sol.id][1]
				if qty_delivered_change > 0:
					sol._move_qty(qty_delivered_change, stock_location, rented_location)
				elif qty_delivered_change < 0:
					sol._return_qty(-qty_delivered_change, stock_location, rented_location)

				if qty_returned_change > 0.0:
					sol._move_qty(qty_returned_change, rented_location, stock_location)
				elif qty_returned_change < 0.0:
					sol._return_qty(-qty_returned_change, rented_location, stock_location)

		# TODO constraint s.t. qty_returned cannot be > than qty_delivered (and same for lots)
		return res

class RentalOrder(models.Model):
	_inherit = 'sale.order'

	rental_status = fields.Selection([
		('draft', 'Quotation'),
		('sent', 'Quotation Sent'),
		('reg_manag', 'Espera de aprobación Gerencia Regional'),
		('fin_approve', 'Espera de aprobación de Finanzas'),
		('pickup', 'Reserved'),
		('return', 'Picked-up'),
		('returned', 'Returned'),
		('cancel', 'Cancelled')],
		string="Rental Status",
		compute='_compute_rental_status',
		store=True
	)