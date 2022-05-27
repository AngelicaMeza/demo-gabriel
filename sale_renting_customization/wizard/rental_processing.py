# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class RentalProcessingLine(models.TransientModel):
    _inherit = 'rental.order.wizard.line'

    def _default_wizard_line_vals(self, line, status):
        default_line_vals = super(RentalProcessingLine, self)._default_wizard_line_vals(line, status)

        default_line_vals.update({
            'tracking': line.product_id.tracking,
        })

        pickeable_lots = self.env['stock.production.lot']
        returnable_lots = self.env['stock.production.lot']
        reserved_lots = line.reserved_lot_ids
        pickedup_lots = line.pickedup_lot_ids
        returned_lots = line.returned_lot_ids

        if status == 'pickup':
            if line.product_id.tracking == 'serial':
                # If product is tracked by serial numbers
                # Get lots in stock:
                rentable_lots = self.env['stock.production.lot']._get_available_lots(line.product_id, line.order_id.warehouse_id.location_for_rental)
                # Get lots reserved/pickedup and not already returned
                rented_lots = line.product_id._get_unavailable_lots(
                    fields.Datetime.now(),
                    line.return_date,
                    ignored_soline_id=line.id,
                    warehouse_id=line.order_id.warehouse_id.id)

                # Don't show reserved lots if they aren't back (or were moved by another app)
                if pickedup_lots:
                    # As we ignored current SaleOrderLine for availability, we need to add
                    # its pickedup_lots to the rented ones to make sure it cannot be picked-up twice.
                    rented_lots += pickedup_lots

                if returned_lots:
                    """As returned lots are considered available, in case of partial pickup+return
                    We could pickup X, return X and then X would always be available for pickup
                    As this would bring problems of quantities and other unexpected behavior
                    We consider that returned serial numbers cannot be picked up again
                    for the same order_line."""
                    rented_lots += returned_lots

                pickeable_lots = rentable_lots - rented_lots

                # Don't count
                # * unavailable lots
                # * lots expected to go to another client before
                # as reserved lots (which will be auto-filled as pickedup_lots).
                reserved_lots = reserved_lots & pickeable_lots
                default_line_vals.update({
                    'qty_delivered': len(reserved_lots),
                })

            if line.product_id.type == 'product':
                default_line_vals.update({
                    'qty_available': line.product_id.with_context(
                        from_date=max(line.reservation_begin, fields.Datetime.now()),
                        to_date=line.return_date,
                        warehouse_id=line.order_id.warehouse_id.id).qty_available,
                    'is_product_storable': True
                })
                # On pickup: only show quantity currently available
                # because the unavailable qty is in company_id.rental_loc_id.

            default_line_vals.update({
                'pickedup_lot_ids': [(6, 0, reserved_lots.ids)],
                'returned_lot_ids': [(6, 0, returned_lots.ids)],
                'pickeable_lot_ids': [(6, 0, pickeable_lots.ids)],
                'returnable_lot_ids': [(6, 0, returnable_lots.ids)]
            })
        elif status == 'return':
            returnable_lots = pickedup_lots - returned_lots
            default_line_vals.update({
                'pickedup_lot_ids': [(6, 0, pickedup_lots.ids)],
                'returned_lot_ids': [(6, 0, returnable_lots.ids)],
                'pickeable_lot_ids': [(6, 0, pickeable_lots.ids)],
                'returnable_lot_ids': [(6, 0, returnable_lots.ids)]
            })

        return default_line_vals