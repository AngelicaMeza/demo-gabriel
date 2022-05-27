# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class HelpdeskSLA(models.Model):
	_inherit = "helpdesk.sla"
	
	cluster_ids = fields.Many2many('segmentation.cluster', string='Cluster', required=True, ondelete="restrict")

class HelpdeskStage(models.Model):
	_inherit = 'helpdesk.stage'

	is_sub_stage = fields.Boolean(string='Etapa resolutora')
	active = fields.Boolean('Active', default=True)

class HelpdeskTeam(models.Model):
	_inherit = "helpdesk.team"

	def _determine_stage(self):
		""" Get a dict with the stage (per team) that should be set as first to a created ticket
			:returns a mapping of team identifier with the stage (maybe an empty record).
			:rtype : dict (key=team_id, value=record of helpdesk.stage)
		"""
		result = dict.fromkeys(self.ids, self.env['helpdesk.stage'])
		for team in self:
			result[team.id] = self.env['helpdesk.stage'].search([('team_ids', 'in', team.id), ('is_sub_stage', '=', False)], order='sequence', limit=1)
		return result