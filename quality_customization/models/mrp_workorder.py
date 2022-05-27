# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class MrpProductionWorkcenterLine(models.Model):
	_inherit = 'mrp.workorder'

	check_point_line = fields.Many2many('check.point.line', related="current_quality_check_id.check_point_line")

	inv = fields.Boolean()

	@api.onchange('check_point_line')
	def pass_fail_buttons(self):
		if any(line.check_yes == line.check_no for line in self.check_point_line):
			self.inv = False
		else:
			self.inv = True
	
	# if the quality check dont have lot/serial number, its set the number of the finished product 
	def open_tablet_view(self):
		if not self.current_quality_check_id.lot_id:
			self.current_quality_check_id.lot_id = self.finished_lot_id
		return super(MrpProductionWorkcenterLine, self).open_tablet_view()

	# When the quality check process its successful, view the successful message
	def _next(self, continue_production=False):
		self.ensure_one()
		old_check_id = self.current_quality_check_id
		result = super(MrpProductionWorkcenterLine, self)._next(continue_production=continue_production)
		if old_check_id.quality_state == 'pass' and old_check_id.point_id:
			return old_check_id.show_successful_message()
		return result
		
	# Create checks for the manufacturing process, if the product have a quality check, see the checklist of the quality point
	def _create_checks(self):
		for wo in self:
			# Track components which have a control point
			processed_move = self.env['stock.move']

			production = wo.production_id
			points = self.env['quality.point'].search([('operation_id', '=', wo.operation_id.id),
													   ('picking_type_id', '=', production.picking_type_id.id),
													   ('company_id', '=', wo.company_id.id),
													   '|', ('product_id', '=', production.product_id.id),
													   '&', ('product_id', '=', False), ('product_tmpl_id', '=', production.product_id.product_tmpl_id.id)])

			move_raw_ids = wo.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel'))
			move_finished_ids = wo.move_finished_ids.filtered(lambda m: m.state not in ('done', 'cancel'))
			values_to_create = []
			for point in points:
				# Check if we need a quality control for this point
				if point.check_execute_now():
					# Check point list for the check process
					aux_checks = []
					if point.check_list_format:
						for check in point.check_point_line:
							aux_checks.append((0, 0, {
									'name': check.name,
									'check_yes': False,
									'check_no': False,
									'description': False
								}))
							
					moves = self.env['stock.move']
					values = {
						'workorder_id': wo.id,
						'point_id': point.id,
						'team_id': point.team_id.id,
						'company_id': wo.company_id.id,
						'product_id': production.product_id.id,
						# Two steps are from the same production
						# if and only if the produced quantities at the time they were created are equal.
						'finished_product_sequence': wo.qty_produced,
						'check_point_line': aux_checks,
					}
					if point.test_type == 'register_byproducts':
						moves = move_finished_ids.filtered(lambda m: m.product_id == point.component_id)
					elif point.test_type == 'register_consumed_materials':
						moves = move_raw_ids.filtered(lambda m: m.product_id == point.component_id)
					else:
						values_to_create.append(values)
					# Create 'register ...' checks
					for move in moves:
						check_vals = values.copy()
						check_vals.update(wo._defaults_from_workorder_lines(move, point.test_type))
						values_to_create.append(check_vals)
					processed_move |= moves

			# Generate quality checks associated with unreferenced components
			moves_without_check = ((move_raw_ids | move_finished_ids) - processed_move).filtered(lambda move: move.has_tracking != 'none')
			quality_team_id = self.env['quality.alert.team'].search([], limit=1).id
			for move in moves_without_check:
				values = {
					'workorder_id': wo.id,
					'product_id': production.product_id.id,
					'company_id': wo.company_id.id,
					'component_id': move.product_id.id,
					'team_id': quality_team_id,
					# Two steps are from the same production
					# if and only if the produced quantities at the time they were created are equal.
					'finished_product_sequence': wo.qty_produced,
				}
				if move in move_raw_ids:
					test_type = self.env.ref('mrp_workorder.test_type_register_consumed_materials')
				if move in move_finished_ids:
					test_type = self.env.ref('mrp_workorder.test_type_register_byproducts')
				values.update({'test_type_id': test_type.id})
				values.update(wo._defaults_from_workorder_lines(move, test_type.technical_name))
				values_to_create.append(values)

			self.env['quality.check'].create(values_to_create)
			# Set default quality_check
			wo.skip_completed_checks = False
			wo._change_quality_check(position=0)

