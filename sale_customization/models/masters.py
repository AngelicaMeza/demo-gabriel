from odoo import models, fields, api, exceptions
import datetime



class sale_event(models.Model):
	_name = 'sale.event'
	_description = 'Event'

	name= fields.Char(string = "Nombre")