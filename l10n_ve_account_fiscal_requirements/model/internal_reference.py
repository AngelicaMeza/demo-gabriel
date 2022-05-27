from odoo import fields, models, api
from odoo.exceptions import ValidationError

class ProductProduct(models.Model):

    # Heredando del modelo product template
    _inherit = 'product.product'

    # Agregando la propiedad required para que el campo sea obligatorio
    default_code = fields.Char(required=False)

    # Restriccion para que la referencia interna sea unica
    _sql_constraints = [
        ('default_code_unique', 'unique (default_code)', 'La referencia interna del producto deber ser unica!')
    ]

    # @api.constrains('default_code')
    # def _check_unique_default_code(self):
    #     for product in self:
    #          count = self.search_count([('default_code', '=', product.default_code), ('id', '!=', product.id)])
    #          if count > 0:
    #              raise ValidationError('La referencia interna del producto deber ser unica!')

class ProductTemplate(models.Model):

    # Heredando del modelo product template
    _inherit = 'product.template'

    # Agregando la propiedad required para que el campo sea obligatorio
    default_code = fields.Char(required=False)

    # Restriccion para que la referencia interna sea unica
    _sql_constraints = [
        ('default_code_unique', 'unique (default_code)', 'La referencia interna del producto deber ser unica!')
    ]

    # @api.constrains('default_code')
    # def _check_unique_default_code(self):
    #     for product in self:
    #          count = self.search_count([('default_code', '=', product.default_code), ('id', '!=', product.id)])
    #          if count > 0:
    #              raise ValidationError('La referencia interna del producto deber ser unica!')