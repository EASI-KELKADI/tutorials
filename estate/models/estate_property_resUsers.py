from odoo import api, fields, models

class User(models.Model):
    _inherit = 'res.users'

    property_ids = fields.One2many(
        'estate.property',
        'salesperson_id',
        string='Property',
        domain=[('state','not in', ['sold','canceled'])]
    )