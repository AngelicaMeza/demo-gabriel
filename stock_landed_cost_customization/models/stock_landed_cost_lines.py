from odoo import api, fields, models


class LandedCostLine(models.Model):
    _inherit = "stock.landed.cost.lines"

    split_method = fields.Selection(default='by_current_cost_price')
