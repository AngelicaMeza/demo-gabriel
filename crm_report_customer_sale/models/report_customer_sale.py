# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class CrmReportCustomerSale(models.Model):
	_name = 'crm.report.customer'
	_table ='crm_report_customer'
	_auto = False
	_description = 'crm_report_customer_sale'

	partner_id = fields.Many2one('res.partner', string='Cliente', readonly=True )
	affiliated = fields.Char(string="Numero de afiliación", readonly=True)
	status_customer = fields.Selection([
		('1', 'ACTIVO'),
		('0', 'INACTIVO'),],
		string="Estado afiliación",
		readonly=True
	)
	code_categ_id = fields.Many2one('code.category', string='Categoría comercial')
	invoice = fields.Char(string='Factura', readonly=True)
	date =fields.Date(string='Fecha', readonly=True)
	product_id = fields.Many2one('product.product', string="Producto", readonly=True)
	quantity = fields.Float(string="Cantidad", readonly=True)
	product_uom_id = fields.Many2one('uom.uom', string="Unidad", readonly=True)
	lot_id = fields.Many2one('stock.production.lot', string="Lotes/Números de serie", readonly=True)
	condition_id = fields.Many2one('condition.stock', string='Condición', readonly=True)
	status_id = fields.Many2one('status.stock', string="Estatus", readonly=True)
	user_id = fields.Many2one('res.users', string="Ejecutivo de cartera", readonly=True)

	def init(self):
		tools.drop_view_if_exists(self._cr, self._table)
		self._cr.execute("""
			CREATE OR REPLACE VIEW %s AS (
				SELECT
					ml.id AS id,
					m.partner_id AS partner_id,
					p.affiliated AS affiliated,
					p.status_customer AS status_customer,
					p.code_categ_id AS code_categ_id,
					m.name AS invoice,
					m.date AS date,
					ml.product_id AS product_id,
					ml.quantity AS quantity,
					ml.product_uom_id AS product_uom_id,
					lot.id AS lot_id,
					lot.condition_id AS condition_id,
					lot.status_id AS status_id,
					p.user_id AS user_id

				FROM
					res_partner AS p

				JOIN account_move AS m ON m.partner_id = p.id
				LEFT JOIN account_move_line AS ml ON ml.move_id = m.id
				LEFT JOIN stock_production_lot AS lot ON lot.id = ml.lot_id

				WHERE 
					m.type = 'out_invoice' and
					m.state = 'posted' and
					ml.credit > '0'
			)""" % (self._table)
		)