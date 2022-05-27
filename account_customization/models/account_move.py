# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
	_inherit = "account.move"
	
	# add fields
	original_invoice_scan = fields.Binary(string="Escáner de factura original", attachment=True, copy=False)
	delivery_note = fields.Binary(string="Nota de entrega", attachment=True, copy=False)
	Compliance_service_received = fields.Binary(string="Soporte de conformidad del servicio recibido", attachment=True, copy=False)
	negotiation_type = fields.Many2one('crm.negotiation', string="Tipo de negociación", compute='compute_negotiation_type', ondelete="restrict")
	partner_id = fields.Many2one(copy=False)

	# add negotiation type to invoice
	def compute_negotiation_type(self):
		origin = self.env['sale.order'].search([('name', '=', self.invoice_origin)], limit=1)
		self.negotiation_type = origin.type_negotiation_id

	def action_post(self):
		if self.type in ['in_invoice', 'out_invoice'] and self.invoice_line_ids.filtered(lambda l: not (l.analytic_account_id or l.analytic_tag_ids)):
			raise ValidationError(_("Invoice lines require a analytic account or a analytic tag to be post."))
		return super(AccountMove, self).action_post()