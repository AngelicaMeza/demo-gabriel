# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class QualityCheck(models.Model):
	_inherit = "quality.check"
	_description = "Quality Check"

	check_point_line = fields.Many2many('check.point.line')

	# set check list 
	@api.onchange('point_id')
	def _set_quality_checks(self):
		aux_checks = []
		self.check_point_line = [(5, 0, 0)]
		if self.point_id.check_list_format:
			for check in self.point_id.check_point_line:
				aux_checks.append((0, 0, {
						'sequence': check.sequence,
						'name': check.name,
						'check_yes': False,
						'check_no': False,
						'description': False
					}))
		self.check_point_line = aux_checks

	inv = fields.Boolean()

	@api.onchange('check_point_line')
	def pass_fail_buttons(self):
		if any(line.check_yes == line.check_no for line in self.check_point_line):
			self.inv = False
		else:
			self.inv = True

	# add successful message
	def redirect_after_pass_fail(self):
		check = self[0]
		if check.quality_state =='fail' and check.test_type in ['passfail', 'measure']:
			return self.show_failure_message()
		if check.quality_state =='pass' and check.test_type in ['passfail', 'measure']:
			return self.show_successful_message()
		if check.picking_id:
			checkable_products = check.picking_id.mapped('move_line_ids').mapped('product_id')
			checks = self.picking_id.check_ids.filtered(lambda x: x.quality_state == 'none' and x.product_id in checkable_products)
			if checks:
				action = self.env.ref('quality_control.quality_check_action_small').read()[0]
				action['res_id'] = checks.ids[0]
				return action
		return super(QualityCheck, self).redirect_after_pass_fail()

	def show_successful_message(self):
		return {
			'name': _('Quality Check successful'),
			'type': 'ir.actions.act_window',
			'res_model': 'quality.check',
			'view_mode': 'form',
			'view_id': self.env.ref('quality_customization.quality_check_view_form_success').id,
			'target': 'new',
			'res_id': self.id,
			'context': self.env.context,
		}