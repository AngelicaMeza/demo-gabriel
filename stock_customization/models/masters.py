# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class BrandStockLine(models.Model):
	_name = 'brand.stock.line'
	_description = 'Brand product type'

	name = fields.Char('Name', required=True)
	code = fields.Char('Code', required=True)

	_sql_constraints = [
		('unique_code', 'unique (code)', "Duplicate code."),
	]

class brand_stock(models.Model):
	_name = 'brand.stock'
	_description = 'Brand'

	name = fields.Char(string = "Nombre", required=True)
	product_types = fields.Many2many('brand.stock.line', string='Aplica a')
	active = fields.Boolean('Active', default=True)

	_sql_constraints = [
		('unique_brand', 'unique (name)', "Duplicate brand."),
	]

class condition_stock(models.Model):
	_name = 'condition.stock'
	_description = 'Condition'

	name = fields.Char(string = "Nombre", required=True)
	default = fields.Boolean(string='Default condition', default=False)
	active = fields.Boolean('Active', default=True)

	_sql_constraints = [
		('unique_condition', 'unique (name)', "Duplicate condition."),
	]

	@api.constrains('default')
	def _constrains_default(self):
		if self.default:
			condition = self.search([('id', '!=', self.id), ('default', '=', True)], limit=1)
			if condition:
				raise ValidationError(_('Condition "%s" is default already !!!' % condition.name))

class status_stock(models.Model):
	_name = 'status.stock'
	_description = 'Status'

	name = fields.Char(string = "Nombre", required=True)
	active = fields.Boolean('Active', default=True)

	_sql_constraints = [
		('unique_status', 'unique (name)', "Duplicate status."),
	]

class Couriers(models.Model):
	_name = 'stock.courier'
	_description = 'Couriers'

	name = fields.Char(string='Courier', required=True)
	code = fields.Integer(string='Code', readonly=True, copy=False)
	active = fields.Boolean('Active', default=True)

	@api.model_create_multi
	def create(self, vals_list):
		res = super(Couriers, self).create(vals_list)
		for rec in res:
			rec.code = self.env['ir.sequence'].next_by_code('stock.courier')
		return res

	_sql_constraints = [
		('unique_status', 'unique (name)', "Duplicate courier."),
		('unique_status', 'unique (code)', "Duplicate code.")
	]