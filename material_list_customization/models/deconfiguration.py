from odoo import models, fields, api, exceptions, _


class location_inherit(models.Model):
    _inherit = 'stock.location'
    deconfiguration_location = fields.Boolean(string="It's a location for deconfiguration?")

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        self.ensure_one()
        res = super(StockPicking, self).button_validate()
        #Desconfigura el lote si la ubicacion destino esta configurada para ello 
        if self.location_dest_id.deconfiguration_location:
            for line in self.move_line_ids_without_package:
                if line.product_id.product_type == '0':
                    line.lot_id.is_configured = False
        return res
