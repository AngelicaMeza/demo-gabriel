# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class HelpdeskSubStages(models.Model):
	_inherit = "helpdesk.substage"

	outsourcing = fields.Boolean(string='Visible to outsourcing', default=False)

class HelpdeskTicketType(models.Model):
	_inherit = 'helpdesk.ticket.type'

	task_type_id = fields.Many2one('fsm.task.type', string='Task type', ondelete="restrict")

class HelpdeskTicket(models.Model):
	_inherit = 'helpdesk.ticket'

	def action_generate_fsm_task(self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'name': _('Create a Field Service task'),
			'res_model': 'helpdesk.create.fsm.task',
			'view_mode': 'form',
			'target': 'new',
			'context': {
				'default_partner_id': self.partner_id.id if self.partner_id else False,
				'default_helpdesk_ticket_id': self.id,
				'default_name': '%s (#%s)' % (self.name, self.id),
			}
		}