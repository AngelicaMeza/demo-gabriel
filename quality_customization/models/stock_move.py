# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, models, _
from odoo.exceptions import UserError

class StockMove(models.Model):
	_inherit = "stock.move"
	
	def _create_quality_checks(self):
		pass

	def _action_assign(self):
		super(StockMove, self)._action_assign()
		
		for rec in self:
			rec._create_quality_checks2()
	
	def _create_quality_checks2(self):
		# Used to avoid duplicated quality points
		quality_points_list = set([])

		# add the pickings for the move in self
		pick_moves = defaultdict(lambda: self.env['stock.move'])
		for move in self:
			pick_moves[move.picking_id] |= move

		for picking, moves in pick_moves.items():
			# adds existing control points to a set so as not to repeat them
			for check in picking.sudo().check_ids:
				point_key = (check.picking_id.id, check.point_id.id, check.team_id.id, check.product_id.id, check.lot_id)
				quality_points_list.add(point_key)
			
			# find the control points that correspond to the products in the picking lines and the type of picking
			quality_points = self.env['quality.point'].sudo().search([
				('picking_type_id', '=', picking.picking_type_id.id),
				'|', ('product_id', 'in', moves.mapped('product_id').ids),
				'&', ('product_id', '=', False), ('product_tmpl_id', 'in', moves.mapped('product_id').mapped('product_tmpl_id').ids)])
			

			for point in quality_points:
				if point.check_execute_now():
					aux_checks = []
					if point.check_list_format:
						for check in point.check_point_line:
							aux_checks.append((0, 0, {
									'name': check.name,
									'check_yes': False,
									'check_no': False,
									'description': False
								}))

					if point.product_id:
						#native behavior for untracked products
						if point.product_id.tracking == 'none':
							point_key = (picking.id, point.id, point.team_id.id, point.product_id.id)
							if point_key in quality_points_list:
								continue
							self.env['quality.check'].sudo().create({
								'picking_id': picking.id,
								'point_id': point.id,
								'team_id': point.team_id.id,
								'product_id': point.product_id.id,
								'company_id': picking.company_id.id,
								'check_point_line': aux_checks,
							})
							quality_points_list.add(point_key)
						# behavior with batch and serial tracking
						else:
							for line in move.move_line_ids.filtered(lambda s: s.product_id == point.product_id ):
								point_key = (picking.id, point.id, point.team_id.id, point.product_id.id, line.lot_id)
								if point_key in quality_points_list or not line.lot_id:
									continue
								self.env['quality.check'].sudo().create({
									'picking_id': picking.id,
									'point_id': point.id,
									'team_id': point.team_id.id,
									'product_id': point.product_id.id,
									'company_id': picking.company_id.id,
									'lot_id': line.lot_id.id,
									'check_point_line': aux_checks,
								})
								quality_points_list.add(point_key)

					# behavior if you do not have a product variant
					else:
						products = picking.move_lines.filtered(lambda move: move.product_id.product_tmpl_id == point.product_tmpl_id).mapped('product_id')
						for product in products:
							if product.tracking == 'none':
								point_key = (picking.id, point.id, point.team_id.id, product.id)
								if point_key in quality_points_list:
									continue
								self.env['quality.check'].sudo().create({
									'picking_id': picking.id,
									'point_id': point.id,
									'team_id': point.team_id.id,
									'product_id': product.id,
									'company_id': picking.company_id.id,
									'check_point_line': aux_checks,
								})
								quality_points_list.add(point_key)
							else:
								for line in move.move_line_ids.filtered(lambda s: s.product_id == product):
									point_key = (picking.id, point.id, point.team_id.id, product.id, line.lot_id)
									if point_key in quality_points_list or not line.lot_id:
										continue
									self.env['quality.check'].sudo().create({
										'picking_id': picking.id,
										'point_id': point.id,
										'team_id': point.team_id.id,
										'product_id': product.id,
										'company_id': picking.company_id.id,
										'lot_id': line.lot_id.id,
										'check_point_line': aux_checks,
									})
									quality_points_list.add(point_key)