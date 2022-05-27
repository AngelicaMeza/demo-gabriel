# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountMove(models.Model):
	_inherit = "account.move"

	dollar_currency_id = fields.Many2one('res.currency', store=True, readonly=True, compute='_compute_amount_dollar')
	amount_untaxed_dollar = fields.Monetary(string='Impuesto excluido en $', store=True, readonly=True, compute='_compute_amount_dollar')
	amount_tax_dollar = fields.Monetary(string='Impuesto en $', store=True, readonly=True, compute='_compute_amount_dollar')
	amount_residual_dollar = fields.Monetary(string='Importe adeudado en $', store=True, compute='_compute_amount_dollar')
	amount_total_dollar = fields.Monetary(string='Total en $', store=True, readonly=True, compute='_compute_amount_dollar')

	@api.depends(
		'amount_untaxed',
		'amount_tax',
		'amount_residual',
		'amount_total',
		'currency_id'
	)
	def _compute_amount_dollar(self):
		for invoice_id in self:

			invoice_id.dollar_currency_id = self.env['res.currency'].search([('name','=','USD'),('id','=',2),('symbol','=','$')])

			if invoice_id.currency_id == invoice_id.company_currency_id:
				invoice_id.amount_untaxed_dollar = 0.0
				invoice_id.amount_tax_dollar = 0.0
				invoice_id.amount_residual_dollar = 0.0
				invoice_id.amount_total_dollar = 0.0
			
			else:
				invoice_id.amount_untaxed_dollar = invoice_id.amount_untaxed
				invoice_id.amount_tax_dollar = invoice_id.amount_tax
				invoice_id.amount_residual_dollar = invoice_id.amount_residual
				invoice_id.amount_total_dollar = invoice_id.amount_total