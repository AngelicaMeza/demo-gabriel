# -*- coding: utf-8 -*-

from odoo import models, fields, _
from itertools import groupby
from odoo.exceptions import AccessError, UserError

class SaleOrder(models.Model):
	_inherit = "sale.order"

	def _create_invoices(self, grouped=False, final=False):
		"""
		Create the invoice associated to the SO.
		:param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
						(partner_invoice_id, currency)
		:param final: if True, refunds will be generated if necessary
		:returns: list of created invoices
		"""
		if not self.env['account.move'].check_access_rights('create', False):
			try:
				self.check_access_rights('write')
				self.check_access_rule('write')
			except AccessError:
				return self.env['account.move']

		# 1) Create invoices.
		invoice_vals_list = []
		for order in self:

			invoice_vals = order._prepare_invoice()
			invoiceable_lines = order._get_invoiceable_lines(final)

			if not invoiceable_lines and not invoice_vals['invoice_line_ids']:
				raise UserError(_('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))
			
			"""Se toman las lineas unicamente de los picking donde su tipo de operacion sea 'Envio' y este en estado 'Realizado'"""
			stock_move_lines = self.env['stock.move.line']
			for stock_move_line in order.picking_ids.filtered(lambda p: p.picking_type_id.code == 'outgoing' and p.state == 'done'):
				stock_move_lines += stock_move_line.move_line_ids_without_package.filtered(lambda l: l.lot_id and not l.lot_id.invoiced)

			"""Agrupamos por lote y asignamos a cada uno su producto asociado y las cantidades enviadas"""
			group_by_lot = []
			for lot_id in stock_move_lines.mapped('lot_id'):
				qty = sum(line.qty_done for line in stock_move_lines.filtered(lambda l: l.lot_id == lot_id))
				group_by_lot.append({
					'lot_id': lot_id,
					'product_id': lot_id.product_id,
					'qty_done': qty,
					'qty_taken': qty
				})

			prepared_invoice_lines = []
			for line in invoiceable_lines:
				qty_to_invoice = line.qty_to_invoice
				if group_by_lot and line.product_id.tracking != 'none':
					for group_by_lot_line in group_by_lot:
						if line.product_id.id == group_by_lot_line['product_id'].id and group_by_lot_line['qty_taken'] > 0:
							if group_by_lot_line['qty_taken'] - qty_to_invoice <= 0:
								prepared_line = line._prepare_invoice_line()
								prepared_line['lot_id'] = group_by_lot_line['lot_id']
								prepared_line['quantity'] = group_by_lot_line['qty_done']
								prepared_invoice_lines.append((0, 0, prepared_line))
								qty_to_invoice -= group_by_lot_line['qty_taken']
								group_by_lot_line['qty_taken'] = 0
								if group_by_lot_line['lot_id'].product_qty == 0:
									group_by_lot_line['lot_id'].sudo().write({'invoiced': True})
							else:
								group_by_lot_line['qty_taken'] -= qty_to_invoice
								qty_to_invoice = 0
						if qty_to_invoice == 0: break
					group_by_lot = [group_by_lot_line for group_by_lot_line in group_by_lot if group_by_lot_line['qty_taken'] > 0]
				if qty_to_invoice > 0:
					prepared_line = line._prepare_invoice_line()
					prepared_line['quantity'] = line.qty_to_invoice
					prepared_invoice_lines.append((0, 0, prepared_line))

			invoice_vals['invoice_line_ids'] += prepared_invoice_lines
			
			# there is a chance the invoice_vals['invoice_line_ids'] already contains data when
			# another module extends the method `_prepare_invoice()`. Therefore, instead of
			# replacing the invoice_vals['invoice_line_ids'], we append invoiceable lines into it
			""" invoice_vals['invoice_line_ids'] += [
				(0, 0, line._prepare_invoice_line())
				for line in invoiceable_lines
			] """

			invoice_vals_list.append(invoice_vals)

		if not invoice_vals_list:
			raise UserError(_(
				'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

		# 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
		if not grouped:
			new_invoice_vals_list = []
			invoice_grouping_keys = self._get_invoice_grouping_keys()
			invoice_vals_list = sorted(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys])
			for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
				origins = set()
				payment_refs = set()
				refs = set()
				ref_invoice_vals = None
				for invoice_vals in invoices:
					if not ref_invoice_vals:
						ref_invoice_vals = invoice_vals
					else:
						ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
					origins.add(invoice_vals['invoice_origin'])
					payment_refs.add(invoice_vals['invoice_payment_ref'])
					refs.add(invoice_vals['ref'])
				ref_invoice_vals.update({
					'ref': ', '.join(refs)[:2000],
					'invoice_origin': ', '.join(origins),
					'invoice_payment_ref': len(payment_refs) == 1 and payment_refs.pop() or False,
				})
				new_invoice_vals_list.append(ref_invoice_vals)
			invoice_vals_list = new_invoice_vals_list

		# 3) Create invoices.

		# As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
		# in a single invoice. Example:
		# SO 1:
		# - Section A (sequence: 10)
		# - Product A (sequence: 11)
		# SO 2:
		# - Section B (sequence: 10)
		# - Product B (sequence: 11)
		#
		# If SO 1 & 2 are grouped in the same invoice, the result will be:
		# - Section A (sequence: 10)
		# - Section B (sequence: 10)
		# - Product A (sequence: 11)
		# - Product B (sequence: 11)
		#
		# Resequencing should be safe, however we resequence only if there are less invoices than
		# orders, meaning a grouping might have been done. This could also mean that only a part
		# of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
		if len(invoice_vals_list) < len(self):
			SaleOrderLine = self.env['sale.order.line']
			for invoice in invoice_vals_list:
				sequence = 1
				for line in invoice['invoice_line_ids']:
					line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
					sequence += 1

		# Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
		# sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
		moves = self.env['account.move'].sudo().with_context(default_type='out_invoice').create(invoice_vals_list)

		# 4) Some moves might actually be refunds: convert them if the total amount is negative
		# We do this after the moves have been created since we need taxes, etc. to know if the total
		# is actually negative or not
		if final:
			moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
		for move in moves:
			move.message_post_with_view('mail.message_origin_link',
				values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
				subtype_id=self.env.ref('mail.mt_note').id
			)
		return moves