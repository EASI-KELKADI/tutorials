from odoo import models, fields

class EstatePropertyTag(models.Model):
    _name = 'estate.property.tag'
    _description = 'Estate Property Tag'
    _order = 'name'

    name = fields.Char('Property Tag', required=True)
    color = fields.Integer(string="Color")

    _sql_constraints = [
        ('unique_tag_name', 'UNIQUE(name)', 'The tag name must be unique.')
    ]