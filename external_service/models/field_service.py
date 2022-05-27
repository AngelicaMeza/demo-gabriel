# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class Task(models.Model):
	_inherit = 'project.task'

	# task type
	task_type_id = fields.Many2one('fsm.task.type', string='Task type', ondelete="restrict")
	task_origin = fields.Char('Origin', readonly=True)

	# partner info
	affiliated = fields.Char(related='partner_id.affiliated')
	vat = fields.Char(related='partner_id.vat')
	cluster_id = fields.Many2one('segmentation.cluster', related='partner_id.cluster_id')
	address = fields.Char(related='partner_id.contact_address', string='Dirección')
	denomination = fields.Char(related='partner_id.denomination')
	region_id = fields.Many2one('crm.region', related='partner_id.region_id')
	city = fields.Char(related='partner_id.city')
	phone_one = fields.Char(related='partner_id.phone_one')
	phone_two = fields.Char(related='partner_id.phone_two')
	phone_three = fields.Char(related='partner_id.phone_three')
	portfolio_user = fields.Many2one(related='partner_id.user_id', string='Ejecutivo cartera')

	#########################################################################################
	# helpdesk info
	include_devices = fields.Boolean(related='helpdesk_ticket_id.include_devices')
	product_lot = fields.Many2one(related='helpdesk_ticket_id.product_lot')
	product_id = fields.Many2one(related='helpdesk_ticket_id.product_id')
	product_condition_id = fields.Many2one(related='helpdesk_ticket_id.product_condition_id')
	product_status_id = fields.Many2one(related='helpdesk_ticket_id.product_status_id')
	product_key_version = fields.Many2one(related='helpdesk_ticket_id.product_key_version')
	product_sim_card = fields.Many2one(related='helpdesk_ticket_id.product_sim_card')
	product_network_operator_id = fields.Many2one(related='helpdesk_ticket_id.product_network_operator_id')
	product_negotiation_type_id = fields.Many2one(related='helpdesk_ticket_id.product_negotiation_type_id')
	product_communication_id = fields.Many2many(related='helpdesk_ticket_id.product_communication_id')

	#affiliated
	affiliated_partner_id = fields.Many2one(related='helpdesk_ticket_id.affiliated_partner_id')
	affiliated_affiliated_number = fields.Char(related='helpdesk_ticket_id.affiliated_affiliated_number')
	affiliated_vat = fields.Char(related='helpdesk_ticket_id.affiliated_vat')
	affiliated_address = fields.Char(related='affiliated_partner_id.contact_address')
	affiliated_phone_one = fields.Char(related='affiliated_partner_id.phone_one')
	affiliated_phone_two = fields.Char(related='affiliated_partner_id.phone_two')
	affiliated_phone_three = fields.Char(related='affiliated_partner_id.phone_three')
	affiliated_portfolio_user = fields.Many2one(related='affiliated_partner_id.user_id')
	###########################################################################################

	company_pos_id = fields.Many2one(related="picking_id.company_pos_id", readonly=True, string="Operadora telefónica solicitada")
	is_outsourcing = fields.Boolean(compute="_is_outsourcing")

	def _is_outsourcing(self):
		if self.env.user and self.env.user.has_group('external_service.group_fsm_outsourcing'):
			self.is_outsourcing = True
		else:
			self.is_outsourcing = False

	@api.constrains('active')
	def _valid_outsourcing(self):
		if self.is_outsourcing == True:
			raise ValidationError("No posee los permisos para realizar esta acción")

	#picking lines
	lot_ids = fields.Many2many('stock.production.lot', string='Devices to install', readonly=True)

	#helpdesk failure
	failure = fields.Many2many('helpdesk.failure', related='helpdesk_ticket_id.failure', ondelete='restrict')
	
	#helpdesk substages
	substage_id = fields.Many2one('helpdesk.substage', compute='_compute_substage_id', inverse='_inverse_substage_id', store=False)
	substages = fields.One2many(related='helpdesk_ticket_id.substages')

	@api.depends('helpdesk_ticket_id')
	def _compute_substage_id(self):
		"""
		Sets substage_id to the outsourcing stage that corresponds in the ticket, otherwise set it to False
		"""
		for task in self:
			if task.helpdesk_ticket_id and task.helpdesk_ticket_id.substage_id and task.helpdesk_ticket_id.substage_id.outsourcing:
				task.substage_id = task.helpdesk_ticket_id.substage_id
			else:
				task.substage_id = False

	def _inverse_substage_id(self):
		"""
		Write the substage selected in the task on the ticket bypassing the access rules
		"""
		for task in self:
			if task.substage_id:
				task.helpdesk_ticket_id.sudo().write({'substage_id': task.substage_id})