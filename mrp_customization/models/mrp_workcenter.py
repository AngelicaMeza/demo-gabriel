# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class MrpWorkcenter(models.Model):
	_name = "mrp.workcenter.user.line"
	_description = "Users asign to workcenter"

	def _default_domain_user_id(self):
		return [('groups_id', 'in', self.env.ref('mrp_customization.group_mrp_assign').id)]

	user_id = fields.Many2one('res.users', string='User', domain=lambda self: self._default_domain_user_id(), required=True)
	workcenter_id = fields.Many2one('mrp.workcenter', string='Workcenter')


class MrpWorkcenter(models.Model):
	_inherit = "mrp.workcenter"

	#users asigned
	workcenter_user_ids = fields.One2many('mrp.workcenter.user.line', 'workcenter_id', string='Users')

	def write(self, values):
		"""
		Clean caches to update rules
		"""
		self.clear_caches()
		return super(MrpWorkcenter, self).write(values)