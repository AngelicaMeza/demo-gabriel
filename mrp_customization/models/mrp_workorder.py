# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class MrpProductionWorkcenterLine(models.Model):
	_inherit = 'mrp.workorder'

	def do_finish(self):
		##################################################################
		#run record_production with sudo permitions to bypass access rule
		self.sudo().record_production()
		##################################################################
		# workorder tree view action should redirect to the same view instead of workorder kanban view when WO mark as done.
		if self.env.context.get('active_model') == self._name:
			action = self.env.ref('mrp.action_mrp_workorder_production_specific').read()[0]
			action['context'] = {'search_default_production_id': self.production_id.id}
			action['target'] = 'main'
		else:
			# workorder tablet view action should redirect to the same tablet view with same workcenter when WO mark as done.
			action = self.env.ref('mrp_workorder.mrp_workorder_action_tablet').read()[0]
			action['context'] = {
				'form_view_initial_mode': 'edit',
				'no_breadcrumbs': True,
				'search_default_workcenter_id': self.workcenter_id.id
			}
		action['domain'] = [('state', 'not in', ['done', 'cancel', 'pending'])]
		return action