# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from odoo.exceptions import UserError

class StockMove(models.Model):
	_inherit = "stock.move"

	def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None, owner_id=None, strict=True):
		""" Create or update move lines.
		"""
		self.ensure_one()

		if not lot_id:
			lot_id = self.env['stock.production.lot']
		if not package_id:
			package_id = self.env['stock.quant.package']
		if not owner_id:
			owner_id = self.env['res.partner']

		taken_quantity = min(available_quantity, need)

		# `taken_quantity` is in the quants unit of measure. There's a possibility that the move's
		# unit of measure won't be respected if we blindly reserve this quantity, a common usecase
		# is if the move's unit of measure's rounding does not allow fractional reservation. We chose
		# to convert `taken_quantity` to the move's unit of measure with a down rounding method and
		# then get it back in the quants unit of measure with an half-up rounding_method. This
		# way, we'll never reserve more than allowed. We do not apply this logic if
		# `available_quantity` is brought by a chained move line. In this case, `_prepare_move_line_vals`
		# will take care of changing the UOM to the UOM of the product.
		if not strict:
			taken_quantity_move_uom = self.product_id.uom_id._compute_quantity(taken_quantity, self.product_uom, rounding_method='DOWN')
			taken_quantity = self.product_uom._compute_quantity(taken_quantity_move_uom, self.product_id.uom_id, rounding_method='HALF-UP')

		quants = []
		rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')

		if self.product_id.tracking == 'serial':
			if float_compare(taken_quantity, int(taken_quantity), precision_digits=rounding) != 0:
				taken_quantity = 0

		try:
			with self.env.cr.savepoint():
				if not float_is_zero(taken_quantity, precision_rounding=self.product_id.uom_id.rounding):
					quants = self.env['stock.quant']._update_reserved_quantity(
						self.product_id, location_id, taken_quantity, lot_id=lot_id,
						package_id=package_id, owner_id=owner_id, strict=strict
					)
					
				###############################################################################################
					if(
						self.move_dest_ids and\
						self.move_dest_ids.raw_material_production_id and\
						self.product_id.product_type == '0' and\
						not lot_id
					):
						quants = [quant for quant in quants if quant[0].lot_id.is_configured == False]
				###############################################################################################
		
		except UserError:
			taken_quantity = 0

		# Find a candidate move line to update or create a new one.
		for reserved_quant, quantity in quants:
			to_update = next((line for line in self.move_line_ids if line._reservation_is_updatable(quantity, reserved_quant)), False)
			if to_update:
				uom_quantity = self.product_id.uom_id._compute_quantity(quantity, to_update.product_uom_id, rounding_method='HALF-UP')
				uom_quantity = float_round(uom_quantity, precision_digits=rounding)
				uom_quantity_back_to_product_uom = to_update.product_uom_id._compute_quantity(uom_quantity, self.product_id.uom_id, rounding_method='HALF-UP')
			if to_update and float_compare(quantity, uom_quantity_back_to_product_uom, precision_digits=rounding) == 0:
				to_update.with_context(bypass_reservation_update=True).product_uom_qty += uom_quantity
			else:
				if self.product_id.tracking == 'serial':
					self.env['stock.move.line'].create([self._prepare_move_line_vals(quantity=1, reserved_quant=reserved_quant) for i in range(int(quantity))])
				else:
					self.env['stock.move.line'].create(self._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant))
		return taken_quantity