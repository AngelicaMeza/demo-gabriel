# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class PurchaseRequisition(models.Model):
	_inherit = "purchase.requisition"

	user_confirm = fields.Many2one('res.users', string='Requisitor', copy=False, readonly=True)
	supervisor_approved = fields.Many2one('res.users')
	supervisor_approved_date = fields.Datetime()
	hr_department_id = fields.Many2one('hr.department', readonly=True, string='Department')
	hr_supervisor = fields.Many2one('res.users', readonly=True, string='Department supervisor')
	inv = fields.Boolean(compute='_compute_inv')
	mail_partner_id = fields.Many2one('res.partner')

	@api.depends('hr_supervisor')
	def _compute_inv(self):
		for rec in self:
			if rec.state == 'set_supervisor_approval' and rec.hr_supervisor:
				rec.inv = (rec.hr_supervisor.id != rec.env.user.id and not (rec.env.user.has_group('purchase_confirmation.group_purchase_secondary_approver_requisition')))
			else:
				rec.inv = True

	@api.onchange('vendor_id')
	def _active_supplier(self):
		if self.vendor_id and self.vendor_id.status_supplier == '0':
			raise ValidationError(_('Proveedor %s se encuentra en estado inactivo' % self.vendor_id.name))

	def action_open(self):
		if self.env['ir.config_parameter'].sudo().get_param('purchase_requisition.sent_purchase_order') and len(self.purchase_ids.filtered(lambda s: s.state not in ['draft','cancel'])) < self.company_id.sent_purchase_order_count:
			raise ValidationError(_('El número de cotizaciones enviadas debe ser al menos %s para poder validar el acuerdo de compra.' % self.company_id.sent_purchase_order_count))
		super(PurchaseRequisition, self).action_open()

	def action_done(self):
		if not self.purchase_ids.filtered(lambda s: s.state in ['purchase','done']):
			raise ValidationError(_('Debe existir al menos una orden confirmada para cerrar el acuerdo de compra.'))
		super(PurchaseRequisition, self).action_done()

	def action_in_progress(self):
		self.ensure_one()
		super(PurchaseRequisition, self).action_in_progress()
		self.supervisor_approved = self.env.uid
		self.supervisor_approved_date = datetime.now()

	state = fields.Selection([
		('draft', 'Draft'),
		('ongoing', 'Ongoing'),
		('set_supervisor_approval', 'En espera de aprobación del supervisor'),
		('in_progress', 'Confirmed'),
		('open', 'Bid Selection'),
		('done', 'Closed'),
		('cancel', 'Cancelled')
		],'Status', tracking=True, required=True, copy=False, default='draft')

	state_blanket_order = fields.Selection([
		('draft', 'Draft'),
		('ongoing', 'Ongoing'),
		('set_supervisor_approval', 'En espera de aprobación del supervisor'),
		('in_progress', 'Confirmed'),
		('open', 'Bid Selection'),
		('done', 'Closed'),
		('cancel', 'Cancelled')
		], compute='_set_state')
	
	def need_supervisor_approve(self):
		self.ensure_one()
		self.state = 'set_supervisor_approval'
		#######################################################################
		if self.name == 'New':
			if self.is_quantity_copy != 'none':
				self.name = self.env['ir.sequence'].next_by_code('purchase.requisition.purchase.tender')
			else:
				self.name = self.env['ir.sequence'].next_by_code('purchase.requisition.blanket.order')
		#######################################################################
		self.write({'user_confirm': self._context.get('uid')})
	@api.constrains('user_confirm')
	def _onchange_requisitor(self):
		if self.user_confirm:
			employee = self.env['hr.employee'].search([('user_id', '=', self.user_confirm.id)], limit=1)
			if employee:
				self.hr_department_id = employee.department_id
				self.hr_supervisor = employee.department_id.manager_id.user_id
			if self.state == 'set_supervisor_approval' and self.hr_supervisor and self.hr_supervisor.partner_id.id not in self.message_partner_ids.ids:
				vals = {
					'res_id': self.id,
					'res_model': 'purchase.requisition',
					'partner_id': self.hr_supervisor.partner_id.id
					}
				self.env['mail.followers'].create(vals)
				lang = self.hr_supervisor.partner_id.lang if self.hr_supervisor.partner_id else None
				self.mail_partner_id = self.hr_supervisor.partner_id
				self.with_context(lang=lang)._message_auto_subscribe_notify([self.hr_supervisor.partner_id.id], 'purchase_confirmation.message_group_assigned')
	
	def automatic_close(self):
		if not self.auto_close and self.purchase_ids and self.state == 'open':
			orders = self.purchase_ids.filtered(lambda s: s.state == 'purchase' and s.invoice_ids)
			for order in orders:
				if any(invoice.state == 'posted' for invoice in order.invoice_ids):
					for line in order:
						if line.product_id.type != 'consu':
							self.state = 'done'
							self.auto_close = True
							break

					if self.auto_close == True:
						break
	auto_close = fields.Boolean(compute=automatic_close)

