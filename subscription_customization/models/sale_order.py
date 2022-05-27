# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from dateutil.relativedelta import relativedelta

class SaleOrder(models.Model):
	_inherit = "sale.order"

	def create_subscriptions(self):
		res = []
		if self.is_rental_order or not 'optional_product_ids' in self.env['product.template']._fields:
			res = super(SaleOrder, self).create_subscriptions()
		return res

	def create_subscriptions2(self, to_create):
		res = []
		for order in self:
			# create a subscription for each service 
			for service in to_create:
				if not service.subscription_id:
					values = order._prepare_subscription_data(service.product_id.subscription_template_id)
					values['recurring_invoice_line_ids'] = service._prepare_subscription_line_data()
					values['related_product'] = to_create[service].product_id.id
					values['stock_lot_id'] = to_create[service].id
					values['origin_document'] = self.name
					subscription = self.env['sale.subscription'].sudo().create(values)
					subscription.onchange_date_start()
					res.append(subscription.id)
					service.write({'subscription_id': subscription.id})
					to_create[service].write({'subscription_id': subscription})
					subscription.message_post_with_view(
						'mail.message_origin_link', values={'self': subscription, 'origin': order},
						subtype_id=self.env.ref('mail.mt_note').id, author_id=self.env.user.partner_id.id
					)
		return res

	# def _split_subscription_lines(self):
	# 	"""Split the order line according to subscription templates that must be created."""
	# 	self.ensure_one()
	# 	res = dict()
	# 	new_sub_lines = self.order_line.filtered(lambda l: not l.subscription_id and l.product_id.subscription_template_id and l.product_id.recurring_invoice)
	# 	for line in new_sub_lines:
	# 		res[line.id] = line
	# 	return res

	def action_confirm(self):
		if not self.is_rental_order:
			self.check_product_serv()
			new_sub_lines = self.order_line.filtered(lambda l: not l.subscription_id and l.product_id.subscription_template_id and l.product_id.recurring_invoice)
			for line in new_sub_lines:
				if line.product_uom_qty > 1:
					for i in range(int(line.product_uom_qty)):
						values = {
							'name': line.name,
							'product_id': line.product_id.id,
							'product_template_id': line.product_template_id.id,
							'product_uom_qty': 1,
							'product_uom': line.product_uom.id,
							'price_unit': line.price_unit,
							'order_id': line.order_id.id,
							'tax_id': [(4, line.tax_id.id)] if line.tax_id else False,
						}
						self.env['sale.order.line'].sudo().create(values)

			for line in new_sub_lines:
				if line.product_uom_qty > 1:
					line.sudo().unlink()

		return super(SaleOrder, self).action_confirm()

	@api.constrains('order_line')
	def check_product_serv(self):
		if not self.is_rental_order and 'optional_product_ids' in self.env['product.template']._fields:
			counters = dict()
			for order in self.order_line:
				if order.product_id.type == 'product' and order.product_id.product_type in ['0','1'] and order.product_id.tracking == 'serial' and order.product_id.optional_product_ids:
					for optional in order.product_id.optional_product_ids:
						if optional in counters:
							counters[optional] += order.product_uom_qty
						else:
							counters[optional] = order.product_uom_qty
				
			for order in self.order_line:
				if order.product_id.type == 'service' and order.product_id.recurring_invoice:
					if order.product_template_id in counters:
						counters[order.product_template_id] -= order.product_uom_qty
					else:
						raise exceptions.ValidationError(_("There is a subscription product that is not related to any product in the list."))
			
			for i in list(counters.values()):
				if i > 0:
					raise exceptions.ValidationError(_("Related subscription products are missing"))
				if i < 0: 
					raise exceptions.ValidationError(_("There are more subscription products than related products"))
	
	def approved_regional_management_button(self):
		self.check_product_serv()
		super(SaleOrder, self).approved_regional_management_button()
	
	def approved_regional_management_change(self):
		self.check_product_serv()
		super(SaleOrder, self).approved_regional_management_change()
	
	def action_quotation_send(self):
		self.check_product_serv()
		return super(SaleOrder, self).action_quotation_send()