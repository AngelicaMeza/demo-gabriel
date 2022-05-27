# -*- coding: utf-8 -*-

from odoo import models, fields, api

class portfolioAdvisor(models.Model):
	_name ="portfolio.advisor"

	name = fields.Char(string="Asesor")
	active = fields.Boolean('Active', default=True)

	_sql_constraints = [('advisor_code_uniq', 'unique (name)', 'El código de asesor cartera debe ser único')]