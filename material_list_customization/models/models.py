# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

class MrpBom(models.Model):
    _inherit = 'mrp.bom'
    @api.constrains('product_id', 'product_tmpl_id', 'bom_line_ids')
    def _check_bom_lines(self):
        for bom in self:
            for bom_line in bom.bom_line_ids:
                if bom.product_id:
                    same_product = bom.product_id == bom_line.product_id and bom.product_id.product_type != '0'
                else:
                    same_product = bom.product_tmpl_id == bom_line.product_id.product_tmpl_id and bom.product_tmpl_id.product_type != '0'
                if same_product:
                    raise ValidationError(_("BoM line product %s should not be the same as BoM product.") % bom.display_name)
                if bom.product_id and bom_line.bom_product_template_attribute_value_ids:
                    raise ValidationError(_("BoM cannot concern product %s and have a line with attributes (%s) at the same time.")
                        % (bom.product_id.display_name, ", ".join([ptav.display_name for ptav in bom_line.bom_product_template_attribute_value_ids])))
                for ptav in bom_line.bom_product_template_attribute_value_ids:
                    if ptav.product_tmpl_id != bom.product_tmpl_id:
                        raise ValidationError(
                            _("The attribute value %s set on product %s does not match the BoM product %s.") %
                            (ptav.display_name, ptav.product_tmpl_id.display_name, bom_line.parent_product_tmpl_id.display_name)
                        )

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def post_inventory(self):
        for order in self:
            # In case the routing allows multiple WO running at the same time, it is possible that
            # the quantity produced in one of the workorders is lower than the quantity produced in
            # the MO.

            #######################################################
            for move in order.move_raw_ids:
                if move.quantity_done == 0 and move.product_id.product_type == '0' and move.product_id == order.product_id:
                    move.quantity_done = 1
            #######################################################

            if order.product_id.tracking != "none" and any(
                wo.state not in ["done", "cancel"]
                and float_compare(wo.qty_produced, order.qty_produced, precision_rounding=order.product_uom_id.rounding) == -1
                for wo in order.workorder_ids
            ):
                raise UserError(
                    _(
                        "At least one work order has a quantity produced lower than the quantity produced in the manufacturing order. "
                        + "You must complete the work orders before posting the inventory."
                    )
                )

            if not any(order.move_raw_ids.mapped('quantity_done')):
                raise UserError(_("You must indicate a non-zero amount consumed for at least one of your components"))

            moves_not_to_do = order.move_raw_ids.filtered(lambda x: x.state == 'done')
            moves_to_do = order.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            for move in moves_to_do.filtered(lambda m: m.product_qty == 0.0 and m.quantity_done > 0):
                move.product_uom_qty = move.quantity_done
            # MRP do not merge move, catch the result of _action_done in order
            # to get extra moves.
            moves_to_do = moves_to_do._action_done()
            moves_to_do = order.move_raw_ids.filtered(lambda x: x.state == 'done') - moves_not_to_do
            order._cal_price(moves_to_do)
            moves_to_finish = order.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            moves_to_finish = moves_to_finish._action_done()
            order.workorder_ids.mapped('raw_workorder_line_ids').unlink()
            order.workorder_ids.mapped('finished_workorder_line_ids').unlink()
            order.action_assign()
            consume_move_lines = moves_to_do.mapped('move_line_ids')
            ##########################################################
            for rec in consume_move_lines:
                if not rec.lot_produced_ids and rec.product_id.product_type == '0' and self.product_id == rec.product_id:
                    rec.lot_produced_ids = [(4,rec.lot_id.id)]
            ##########################################################
            for moveline in moves_to_finish.mapped('move_line_ids'):
                if moveline.move_id.has_tracking != 'none' and moveline.product_id == order.product_id or moveline.lot_id in consume_move_lines.mapped('lot_produced_ids'):
                    if any([not ml.lot_produced_ids for ml in consume_move_lines]):
                        raise UserError(_('You can not consume without telling for which lot you consumed it'))
                    # Link all movelines in the consumed with same lot_produced_ids false or the correct lot_produced_ids
                    filtered_lines = consume_move_lines.filtered(lambda ml: moveline.lot_id in ml.lot_produced_ids)
                    moveline.write({'consume_line_ids': [(6, 0, [x for x in filtered_lines.ids])]})
                else:
                    # Link with everything
                    moveline.write({'consume_line_ids': [(6, 0, [x for x in consume_move_lines.ids])]})
        return True

    def button_mark_done(self):
        self.ensure_one()
        self._check_company()
        for wo in self.workorder_ids:
            if wo.time_ids.filtered(lambda x: (not x.date_end) and (x.loss_type in ('productive', 'performance'))):
                raise UserError(_('Work order %s is still running') % wo.name)
        self._check_lots()

        self.post_inventory()
        # Moves without quantity done are not posted => set them as done instead of canceling. In
        # case the user edits the MO later on and sets some consumed quantity on those, we do not
        # want the move lines to be canceled.
        (self.move_raw_ids | self.move_finished_ids).filtered(lambda x: x.state not in ('done', 'cancel')).write({
            'state': 'done',
            'product_uom_qty': 0.0,
        })
        ################################################
        for rec in self.finished_move_line_ids:
            if rec.product_id.product_type == '0':
                rec.lot_id.is_configured = True
        #################################################
        return self.write({'date_finished': fields.Datetime.now()})

    def _generate_workorders(self, exploded_boms):
        workorders = self.env['mrp.workorder']
        original_one = False
        for bom, bom_data in exploded_boms:
            # If the routing of the parent BoM and phantom BoM are the same, don't recreate work orders, but use one master routing
            if bom.routing_id.id and (not bom_data['parent_line'] or bom_data['parent_line'].bom_id.routing_id.id != bom.routing_id.id):
                temp_workorders = self._workorders_create(bom, bom_data)
                #################################################################
                if temp_workorders.product_id.product_type == '0':
                    for rec in temp_workorders.raw_workorder_line_ids:
                        if rec.product_id.product_type == '0' and rec.product_id == temp_workorders.product_id:
                            temp_workorders.finished_lot_id = rec.lot_id
                #######################################################################
                workorders += temp_workorders
                if temp_workorders: # In order to avoid two "ending work orders"
                    if original_one:
                        temp_workorders[-1].next_work_order_id = original_one
                    original_one = temp_workorders[0]
        return workorders

class MrpProductProduce(models.TransientModel):
    _inherit = 'mrp.product.produce'
    @api.onchange('raw_workorder_line_ids')
    def lot_onchange(self):
        for rec in self.raw_workorder_line_ids:
            if rec.lot_id.is_configured == False:
                if rec.product_id == self.product_id and rec.lot_id:
                    self.finished_lot_id = rec.lot_id
            else:
                raise ValidationError('El lote seleccionado ya esta configurado.')

    def do_produce(self):
        """ Save the current wizard and go back to the MO. """
        self.ensure_one()
        self._record_production()
        self._check_company()
        for rec in self.production_id.move_raw_ids.move_line_ids:
            if rec.product_id.product_type == '0' and  not rec.lot_id:
                rec.lot_id += self.finished_lot_id
                rec.lot_produced_ids = [(4,self.finished_lot_id.id)]
        return {'type': 'ir.actions.act_window_close'}

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id:
            self.finished_lot_id = self.lot_id

class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'
    
    is_configured = fields.Boolean(string= "It's configured?")