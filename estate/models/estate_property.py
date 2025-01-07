from datetime import timedelta
from odoo import models, fields,api

class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Estate Property'

    # Basic fields
    name = fields.Char(string='Title', required=True)
    description = fields.Text(string='Description')
    postcode = fields.Char(string='Postcode')
    date_availability = fields.Date(string='Date Available', copy=False, default=fields.Date.today() + timedelta(days=90))
    expected_price = fields.Float(string='Expected Price', required=True)
    selling_price = fields.Float(string='Selling Price', readonly=True, copy=False)
    bedrooms = fields.Integer(string='Number of Bedrooms', default=2)
    living_area = fields.Integer(string='Living Area (m²)')
    facades = fields.Integer(string='Number of Facades')
    garage = fields.Boolean(string='Has Garage')
    garden = fields.Boolean(string='Has Garden')
    garden_area = fields.Integer(string='Garden Area (m²)')
    garden_orientation = fields.Selection([
        ('north', 'North'),
        ('south', 'South'),
        ('east', 'East'),
        ('west', 'West'),
    ], string='Garden Orientation')

    active = fields.Boolean(string='Active', default=True)

    state = fields.Selection([
        ('new', 'New'),
        ('offer_received', 'Offer Received'),
        ('offer_accepted', 'Offer Accepted'),
        ('sold', 'Sold'),
        ('canceled', 'Canceled'),
    ], string='State', required=True, default='new', copy=False)

    property_type_id = fields.Many2one('estate.property.type', string="Property Type", required=True)
    buyer_id = fields.Many2one("res.partner", string="Buyer")
    salesperson_id = fields.Many2one('res.users', string="Salesman",default=lambda self: self.env.user)

    tag_ids = fields.Many2many('estate.property.tag', string="Tags")

    offer_ids = fields.One2many(
        'estate.property.offer', 'property_id', string="Offers"
    )
    best_price = fields.Float(string='Best Offer', compute="_compute_best_price", store=True)
    total_area = fields.Float(string="Total Area", compute="_compute_total_area", store=True)

    @api.depends('living_area','garden_area')
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + (record.garden_area if record.garden_area else 0)

    @api.depends('offer_ids')
    def _compute_best_price(self):
        for record in self:
            record.best_price = max(record.offer_ids.mapped('price'), default=0)

    @api.onchange('garden')
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
        else:
            self.garden_area = 0
            self.garden_orientation = False

    def action_sold(self):
        for record in self:
            if record.state == 'canceled':
                raise ValueError("Canceled")
            record.state = 'sold'

    def action_cancel(self):
        for record in self:
            if record.state == 'sold':
                raise ValueError("Sold")
            record.state = 'canceled'
