# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError

class subscription_custom(models.Model):
	_inherit = 'sale.subscription'

	stock_lot_id = fields.Many2one('stock.production.lot')
	related_product = fields.Many2one('product.product')
	origin_document = fields.Char()
	affiliated = fields.Char()

	@api.model
	def create(self, vals):
		res = super().create(vals)
		res.recurring_next_date = res. date_start
		res.recurring_next_date = fields.Datetime.from_string(res.recurring_next_date) - relativedelta(days=res.recurring_next_date.day-1) 
		res.recurring_next_date = fields.Datetime.from_string(res.recurring_next_date) + relativedelta(months=1)
		return res
	
	@api.constrains('partner_id')
	def _constrains_partner_id(self):
		if self.partner_id:
			self.affiliated = self.partner_id.affiliated

	@api.onchange('partner_id')
	def _onchange_partner_id(self):
		if self.partner_id:
			self.affiliated = self.partner_id.affiliated

	@api.onchange('affiliated')
	def _onchange_affiliated(self):
		if self.affiliated:
			partner = self.env['res.partner'].search([('affiliated', '=', self.affiliated)], limit=1)
			if partner:
					self.partner_id = partner.id
			else:
				raise exceptions.ValidationError('La afiliación ingresada no pertenece a ningun contacto')
	
	@api.constrains('affiliated')
	def _constrains_affiliated(self):
		if self.affiliated and self._context.get('import_file', False):
			partner = self.env['res.partner'].search([('affiliated', '=', self.affiliated)], limit=1)
			if partner:
					self.partner_id = partner.id
			else:
				raise exceptions.ValidationError('La afiliación ingresada no pertenece a ningun contacto')

	@api.constrains('stage_id')
	def _constrains_stage_id(self):
		########################################################################
		if self.stage_id.id == self.env.ref('sale_subscription.sale_subscription_stage_closed').id or self.stage_id.id == self.env.ref('sale_subscription.sale_subscription_stage_draft').id:
			if self.stock_lot_id and self.stock_lot_id.subscription_id:
				self.stock_lot_id.subscription_id = False

		if self.stage_id.id == self.env.ref('sale_subscription.sale_subscription_stage_in_progress').id or self.stage_id.id == self.env.ref('sale_subscription.sale_subscription_stage_upsell').id:
			if self.related_product and self.stock_lot_id:
				self.stock_lot_id.subscription_id = self.id
			else:
				raise UserError('Debe ingresar los campos: producto relacionado a la suscripción y serial del producto.')
		########################################################################

	############################################################################
	@api.onchange('stock_lot_id')
	def _onchange_stock_lot_id(self):
		if self.stock_lot_id.subscription_id:
			raise ValidationError('Este lote ya tiene una suscripción relacionada')
	############################################################################