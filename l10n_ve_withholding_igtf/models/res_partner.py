from odoo import api, fields, models


class ResPartner(models.Model):
	_inherit = 'res.partner'

	is_special_taxpayer_igtf = fields.Boolean(
		help='Indicates that the company is a special taxpayer for' 
		' IGTF withholding.'
	)
