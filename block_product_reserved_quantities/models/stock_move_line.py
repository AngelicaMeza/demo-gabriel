# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round, float_compare
from odoo.tools import OrderedSet




class StockMoveLine(models.Model):
	_inherit = "stock.move.line"

	def _free_reservation(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, ml_to_ignore=None):
		""" When editing a done move line or validating one with some forced quantities, it is
		possible to impact quants that were not reserved. It is therefore necessary to edit or
		unlink the move lines that reserved a quantity now unavailable.

		:param ml_to_ignore: recordset of `stock.move.line` that should NOT be unreserved
		"""
		self.ensure_one()

		if ml_to_ignore is None:
			ml_to_ignore = self.env['stock.move.line']
		ml_to_ignore |= self

		# Check the available quantity, with the `strict` kw set to `True`. If the available
		# quantity is greather than the quantity now unavailable, there is nothing to do.
		available_quantity = self.env['stock.quant']._get_available_quantity(
			product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True
		)
		if quantity > available_quantity:
			if product_id.tracking == 'none':
				return ('\t-[%s] %s en "%s"\n' % (product_id.default_code, product_id.name, location_id.complete_name))
			elif product_id.tracking == 'lot':
				return ('\t-[%s] %s: %s en "%s"\n' % (product_id.default_code, product_id.name, lot_id.name, location_id.complete_name))
			elif product_id.tracking == 'serial':
				return ('\t-[%s] %s: %s en "%s"\n' % (product_id.default_code, product_id.name, lot_id.name, location_id.complete_name))
		else:
			return False

	def _action_done(self):
		""" This method is called during a move's `action_done`. It'll actually move a quant from
		the source location to the destination location, and unreserve if needed in the source
		location.

		This method is intended to be called on all the move lines of a move. This method is not
		intended to be called when editing a `done` move (that's what the override of `write` here
		is done.
		"""
		Quant = self.env['stock.quant']

		# First, we loop over all the move lines to do a preliminary check: `qty_done` should not
		# be negative and, according to the presence of a picking type or a linked inventory
		# adjustment, enforce some rules on the `lot_id` field. If `qty_done` is null, we unlink
		# the line. It is mandatory in order to free the reservation and correctly apply
		# `action_done` on the next move lines.
		ml_ids_to_delete = OrderedSet()
		lot_vals_to_create = []  # lot values for batching the creation
		associate_line_lot = []  # move_line to associate to the lot
		for ml in self:
			# Check here if `ml.qty_done` respects the rounding of `ml.product_uom_id`.
			uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='HALF-UP')
			precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
			qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
			if float_compare(uom_qty, qty_done, precision_digits=precision_digits) != 0:
				raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
									defined on the unit of measure "%s". Please change the quantity done or the \
									rounding precision of your unit of measure.') % (ml.product_id.display_name, ml.product_uom_id.name))

			qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
			if qty_done_float_compared > 0:
				if ml.product_id.tracking != 'none':
					picking_type_id = ml.move_id.picking_type_id
					if picking_type_id:
						if picking_type_id.use_create_lots:
							# If a picking type is linked, we may have to create a production lot on
							# the fly before assigning it to the move line if the user checked both
							# `use_create_lots` and `use_existing_lots`.
							if ml.lot_name and not ml.lot_id:
								lot_vals_to_create.append({'name': ml.lot_name, 'product_id': ml.product_id.id, 'company_id': ml.move_id.company_id.id})
								associate_line_lot.append(ml)
								continue  # Avoid the raise after because not lot_id is set
						elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
							# If the user disabled both `use_create_lots` and `use_existing_lots`
							# checkboxes on the picking type, he's allowed to enter tracked
							# products without a `lot_id`.
							continue
					elif ml.move_id.inventory_id:
						# If an inventory adjustment is linked, the user is allowed to enter
						# tracked products without a `lot_id`.
						continue

					if not ml.lot_id:
						raise UserError(_('You need to supply a Lot/Serial number for product %s.') % ml.product_id.display_name)
			elif qty_done_float_compared < 0:
				raise UserError(_('No negative quantities allowed'))
			else:
				ml_ids_to_delete.add(ml.id)

		mls_to_delete = self.env['stock.move.line'].browse(ml_ids_to_delete)
		mls_to_delete.unlink()

		# Batching the creation of lots and associated each to the right ML (order is preserve in the create)
		lots = self.env['stock.production.lot'].create(lot_vals_to_create)
		for ml, lot in zip(associate_line_lot, lots):
			ml.write({'lot_id': lot.id})

		mls_todo = (self - mls_to_delete)
		mls_todo._check_company()

		# Now, we can actually move the quant.
		ml_ids_to_ignore = OrderedSet()
		error = ""
		for ml in mls_todo:
			if ml.product_id.type == 'product':
				rounding = ml.product_uom_id.rounding

				# if this move line is force assigned, unreserve elsewhere if needed
				if not ml._should_bypass_reservation(ml.location_id) and float_compare(ml.qty_done, ml.product_uom_qty, precision_rounding=rounding) > 0:
					qty_done_product_uom = ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id, rounding_method='HALF-UP')
					extra_qty = qty_done_product_uom - ml.product_qty
					ml_to_ignore = self.env['stock.move.line'].browse(ml_ids_to_ignore)
					no_qty = ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, ml_to_ignore=ml_to_ignore)
					if no_qty:
						error += no_qty
						continue
				# unreserve what's been reserved
				if not ml._should_bypass_reservation(ml.location_id) and ml.product_id.type == 'product' and ml.product_qty:
					Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)

				# move what's been actually done
				quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
				available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
				if available_qty < 0 and ml.lot_id:
					# see if we can compensate the negative quants with some untracked quants
					untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
					if untracked_qty:
						taken_from_untracked_qty = min(untracked_qty, abs(quantity))
						Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
						Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
				Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
			ml_ids_to_ignore.add(ml.id)
		if len(error) > 0:
			raise ValidationError('No existe disponibilidad de la cantidad demandada para los siguientes productos: \n\n'+error)
		# Reset the reserved quantity as we just moved it to the destination location.
		mls_todo.with_context(bypass_reservation_update=True).write({
			'product_uom_qty': 0.00,
			'date': fields.Datetime.now(),
		})
