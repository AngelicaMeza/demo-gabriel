# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class StockPickingType(models.Model):
	_inherit = 'stock.picking.type'

	bills = fields.Boolean('Bills')

class Picking(models.Model):
	_inherit = 'stock.picking'

	incorporate = fields.Boolean(compute='_compute_show_incorporate')
	incorporated_by = fields.Many2one('res.users', 'Incorporated by', readonly=True, copy=False)
	incorporated_date = fields.Datetime('Incorporated date', readonly=True, copy=False)
	state = fields.Selection([
		('draft', 'Draft'),
		('waiting', 'Waiting Another Operation'),
		('confirmed', 'Waiting'),
		('assigned', 'Ready'),
		('incorporated', 'Incorporated'),
		('done', 'Done'),
		('cancel', 'Cancelled'),
	], string='Status', compute='_compute_state',
		copy=False, index=True, readonly=True, store=True, tracking=True,
		help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
			 " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
			 " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
			 " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
			 " * Done: The transfer has been processed.\n"
			 " * Cancelled: The transfer has been cancelled.")

	@api.depends('state', 'is_locked')
	def _compute_show_validate(self):
		for picking in self:
			if not (picking.immediate_transfer) and picking.state == 'draft':
				picking.show_validate = False
			elif picking.state not in ('draft', 'waiting', 'confirmed', 'assigned','incorporated') or not picking.is_locked:
				picking.show_validate = False
			else:
				picking.show_validate = True

	@api.depends('picking_type_id', 'move_line_ids_without_package.product_id', 'state')
	def _compute_show_incorporate(self):
		if(
			self.state in ['confirmed', 'assigned'] and\
			self.picking_type_id and self.picking_type_id.bills and\
			self.move_line_ids_without_package and\
			self.move_line_ids_without_package.filtered(lambda l: l.product_id.product_type == '0')
		):
			self.incorporate = True
		else:
			self.incorporate = False

	def incorporate_button(self):
		context = self._context
		self.write({
			'incorporate': False,
			'incorporated_by': context.get('uid'),
			'incorporated_date': fields.datetime.now(),
			'state': 'incorporated',
		})

	def do_unreserve(self):
		super(Picking, self).do_unreserve()
		for picking in self:
			picking.incorporated_by = False
			picking.incorporated_date = False