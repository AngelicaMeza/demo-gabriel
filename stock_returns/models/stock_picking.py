# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError

class algo(models.Model):
	_inherit = "stock.picking"
	_description = "stock picking"
	
	def action_assign_returns(self, return_picking):
		""" Check availability of picking moves.
		This has the effect of changing the state and reserve quants on available moves, and may
		also impact the state of the picking as it is computed based on move's states.
		@return: True
		"""
		self.filtered(lambda picking: picking.state == 'draft').action_confirm()
		moves = self.mapped('move_lines').filtered(lambda move: move.state not in ('draft', 'cancel', 'done'))
		if not moves:
			raise UserError(_('Nothing to check the availability for.'))
		# If a package level is done when confirmed its location can be different than where it will be reserved.
		# So we remove the move lines created when confirmed to set quantity done to the new reserved ones.
		package_level_done = self.mapped('package_level_ids').filtered(lambda pl: pl.is_done and pl.state == 'confirmed')
		package_level_done.write({'is_done': False})
		moves._action_assign_returns(return_picking)
		package_level_done.write({'is_done': True})
		return True