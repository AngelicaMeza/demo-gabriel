# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	def get_employee_name(self, user_id):
		if user_id:
			if self.env['hr.employee'].search([('user_id', '=', user_id.id)]):
				return self.env['hr.employee'].search([('user_id', '=', user_id.id)], limit=1).name
			else:
				return "_"
		else:
			raise ValidationError(_("La funcion get_employee necesita un usuario"))

	def get_employee_job(self, user_id):
		if user_id:
			if self.env['hr.employee'].search([('user_id', '=', user_id.id)]):
				return self.env['hr.employee'].search([('user_id', '=', user_id.id)], limit=1).job_title
			else:
				return "_"
		else:
			raise ValidationError(_("La funcion get_employee necesita un usuario"))