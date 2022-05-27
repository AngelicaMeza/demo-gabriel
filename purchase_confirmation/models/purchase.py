	# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	state = fields.Selection([
		('draft', 'RFQ'),
		('sent', 'RFQ Sent'),
		('to approve', 'To Approve'),
		('man_approve', 'Espera de aprobación Gerente de Área'),
		('fin_approve', 'Espera de aprobación VP Finanzas'),
		('purchase', 'Purchase Order'),
		('done', 'Locked'),
		('cancel', 'Cancelled')],
		string='Status',
		readonly=True,
		index=True,
		copy=False,
		default='draft',
		tracking=True
	)

	man_approve = fields.Many2one('res.users', string='Aprobado por', copy=False)
	fin_approve = fields.Many2one('res.users', string='Aprobado por', copy=False)
	man_approve_date = fields.Datetime(string="Fecha", readonly=True, copy=False)
	fin_approve_date = fields.Datetime(string="Fecha", readonly=True, copy=False)
	contact_phone = fields.Char(related='user_id.phone_one')
	contact_email = fields.Char(related='user_id.email')
	invoice_locked = fields.Boolean(default=False)
	contact_person = fields.Many2one('res.partner')
	contact_person_supplier = fields.Many2one('res.partner')
	inv = fields.Boolean(compute='_compute_inv')
	mail_partner_id = fields.Many2one('res.partner')

	def update_price(self):
		for line in self.order_line:
			if not line.invoice_lines:
				for seller in line.product_id.seller_ids:
					if seller.name == self.partner_id:
						if seller.currency_id == self.currency_id:
							line.price_unit = seller.price
						else:
							line.price_unit = seller.currency_id._convert(seller.price, self.currency_id, self.company_id, self.date_order or self.date_approve)
						break

	@api.depends('requisition_id.hr_supervisor')
	def _compute_inv(self):
		for rec in self:
			if rec.state == 'man_approve' and rec.requisition_id.hr_supervisor:
				rec.inv = (rec.requisition_id.hr_supervisor.id != rec.env.user.id and not (rec.env.user.has_group('purchase_confirmation.group_purchase_secondary_approver_quotation')))
			else:
				rec.inv = True

	def _add_follower(self, user):
		if user and user.partner_id.id not in self.message_partner_ids.ids:
			vals = {
				'res_id': self.id,
				'res_model': 'purchase.order',
				'partner_id': user.partner_id.id
				}
			self.env['mail.followers'].create(vals)

	def _send_assigned_email(self, user):
		if user:
			lang = user.partner_id.lang if user.partner_id else None
			self.mail_partner_id = user.partner_id
			self.with_context(lang=lang)._message_auto_subscribe_notify([user.partner_id.id], 'purchase_confirmation.message_group_assigned')
	
	@api.constrains('state')
	def _consttraint_state_followers(self):
		if self.state == 'fin_approve':
			for user in self.env['res.users'].search([]).filtered(lambda s: s.has_group('purchase_confirmation.group_purchase_finance_vp_approval') and s.partner_id.id not in self.message_partner_ids.ids):
				self._add_follower(user)
				self._send_assigned_email(user)
		
		if self.state == 'purchase':
			self._send_assigned_email(self.user_id)

		if self.state == 'man_approve':
			self._add_follower(self.requisition_id.hr_supervisor)
			self._send_assigned_email(self.requisition_id.hr_supervisor)

		#######################################################################################3
		if self.state == 'sent' and self.requisition_id:
			self.requisition_id.state = 'open'
		#######################################################################################3

	# ocultar el boton de crear segun condicion
	# x_css = fields.Html(
	# 	string='CSS',
	# 	sanitize=False,
	# 	compute='_compute_css',
	# 	store=False,
	# )
	# @api.depends('state')
	# def _compute_css(self):
	# 	for application in self:
	# 		if application and not self.env.user.has_group('purchase_confirmation.group_purchase_create_button'):
	# 			application.x_css = '<style>.o_form_button_create {display: none !important;}</style>'
	# 		else:
	# 			application.x_css = False

	def unlock_invoice(self):
		self.invoice_locked = False

	@api.onchange('partner_id')
	def _active_supplier(self):
		if self.partner_id and self.partner_id.status_supplier == '0':
			raise ValidationError(_('Proveedor %s INACTIVO' % self.partner_id.name))

	@api.onchange('order_line')
	def service_product(self):
		for line in self.order_line:
			self.invoice_locked = True if line.product_id.type == 'service' else False

	def action_rfq_send(self):
		for order in self.order_line:
			if (order.account_analytic_id.active == False and order.analytic_tag_ids.active == False):
				raise ValidationError('Debe haber al menos una cuenta o una etiqueta analítica por producto.')
		return super(PurchaseOrder, self).action_rfq_send()
	
	def request_VP_approval(self):
		if self.requisition_id and self.requisition_id.purchase_ids.filtered(lambda s: s.state in ['man_approve', 'fin_approve']):
			raise ValidationError(_('Ya existe una solicitud en espera de aprobación en el acuerdo de compra.'))	

		for order in self.order_line:
			if (order.account_analytic_id.active == False and order.analytic_tag_ids.active == False):
				raise ValidationError('Debe haber al menos una cuenta o una etiqueta analítica por producto.')
		message = ""
		if not self.partner_id.cedula:
			message += "* Cedula de Identidad\n"
		if not self.partner_id.rif:
			message += "* R.I.F\n"
		if not self.partner_id.commercial_register:
			message += "* Registro Mercantil\n"
		if not (self.partner_id.commercial_reference and self.partner_id.commercial_reference_2 and self.partner_id.commercial_reference_3):
			message += "* Referencias comerciales\n"
		if not self.partner_id.bank_certification:
			message += "* Certificación Bancaria\n"
		if not self.partner_id.authorization_payment_transfer:
			message += "* Autorización para recibir pago por transferencia"
		
		if message != "":
			raise ValidationError("Debe cargar los siguientes documentos del proveedor:\n" + message)
		
		if self.requisition_id and self.env['ir.config_parameter'].sudo().get_param('purchase_requisition.sent_purchase_order') and len(self.requisition_id.purchase_ids.filtered(lambda s: s.state == 'sent')) < self.company_id.sent_purchase_order_count:
			action = self.env.ref('purchase_confirmation.purchase_order_validation_wizard').read()[0]
			action['context'] = {'purchase_id': self.id, 'default_purchase_number': len(self.requisition_id.purchase_ids.filtered(lambda s: s.state == 'sent')), 'default_conf_num': self.company_id.sent_purchase_order_count}
			return action
		else:
			self.state = 'fin_approve'

	def request_manager_approval(self):
		self.write({'state': 'man_approve'})
		self.fin_approve = self._context.get('uid')
		self.fin_approve_date = datetime.now()
		return True

	def button_approve(self, force=False):
		self.man_approve = self._context.get('uid')
		self.man_approve_date = datetime.now()
		return super(PurchaseOrder, self).button_approve(force)

	def button_confirm(self):
		for order in self:
			if order.state != 'man_approve':
				continue
			order._add_supplier_to_product()
			# Deal with double validation process
			if order.company_id.po_double_validation == 'one_step'\
					or (order.company_id.po_double_validation == 'two_step'\
						and order.amount_total < self.env.company.currency_id._convert(
							order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()))\
					or order.user_has_groups('purchase.group_purchase_manager'):
				order.button_approve()
			else:
				order.write({'state': 'to approve'})
		return True

	def button_cancel(self):
		for rec in self:
			if rec.requisition_id and rec.state == 'sent' and not rec.requisition_id.purchase_ids.filtered(lambda s: s.state == 'purchase'):
				raise ValidationError(_('Debe existir al menos una orden confirmada en el Requisición de compra para cancelar la solicitud.'))
			super(PurchaseOrder, rec).button_cancel()

	def print_quotation(self):
		for order in self.order_line:
			if (order.account_analytic_id.active == False and order.analytic_tag_ids.active == False):
				raise ValidationError('Debe haber al menos una cuenta o una etiqueta analítica por producto.')
		return super(PurchaseOrder, self).print_quotation()

	def get_employee_department_name(self, user_id):
		if user_id:
			if self.env['hr.employee'].search([('user_id', '=', user_id.id)]):
				return self.env['hr.employee'].search([('user_id', '=', user_id.id)], limit=1).department_id.name
			else:
				return "_"
		else:
			raise ValidationError("La funcion get_employee necesita un usuario")
	
	def get_employee_name(self, user_id):
		if user_id:
			if self.env['hr.employee'].search([('user_id', '=', user_id.id)]):
				return self.env['hr.employee'].search([('user_id', '=', user_id.id)], limit=1).name
			else:
				return "_"
		else:
			raise ValidationError("La funcion get_employee necesita un usuario")

	def get_employee_job(self, user_id):
		if user_id:
			if self.env['hr.employee'].search([('user_id', '=', user_id.id)]):
				return self.env['hr.employee'].search([('user_id', '=', user_id.id)], limit=1).job_title
			else:
				return "_"
		else:
			raise ValidationError("La funcion get_employee necesita un usuario")

	def get_lines_list(self):
		lines_list = []
		lines_list.append(self.order_line[0:12])
		for n in range(12, len(self.order_line), 23):
			lines_list.append(self.order_line[n:n+23])
		return lines_list
	
	def get_lines_list_quotation(self):
		lines_list = []
		lines_list.append(self.order_line[0:18])
		for n in range(18, len(self.order_line), 25):
			lines_list.append(self.order_line[n:n+25])
		return lines_list

class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'
	_description = 'Purchase Order Line'

	@api.constrains('qty_invoiced')
	def automatic_state_change(self):
		if self.order_id.requisition_id and self.order_id.state == 'purchase' and self.order_id.requisition_id.state in ['draft', 'in_progress'] :
			# creacion y llenado de diccionario que contiene todos los productos y cantidades que se compraran
			quant = dict()
			for line in self.order_id.requisition_id.line_ids:
				if line.product_id.id in quant:
					quant[line.product_id.id] += line.product_qty
				else:
					quant[line.product_id.id] = line.product_qty
			
			# Vaciado del diccionario de cantidades
			for purchase in self.order_id.requisition_id.purchase_ids:
				if purchase.invoice_ids and purchase.state == 'purchase':
					for line in purchase.order_line:
						if line.product_id.id in quant:
							quant[line.product_id.id] -= line.qty_invoiced
			
			# comporbacion de que el diccionario tenga valores menores que 1
			if all(value < 1 for value in quant.values()):
				self.order_id.requisition_id.state = 'open'
