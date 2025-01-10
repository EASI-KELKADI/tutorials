from odoo import api, models, fields
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero


class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Real estate property'
    _order = 'state asc, id desc'

    name = fields.Char(string='Property name', required=True)
    description = fields.Text(string='Description')
    postcode = fields.Char(string='Postcode')
    date_availability = fields.Date(string='Available from', copy=False,
                                    default=lambda self: datetime.today() + timedelta(days=90))
    expected_price = fields.Float(string='Expected price', required=True)
    selling_price = fields.Float(string='Selling price', readonly=True, copy=False)
    bedrooms = fields.Integer(string='Bedrooms', default=2)
    living_area = fields.Integer(string='Living area (sqm)')
    facades = fields.Integer(string='Facades')
    garage = fields.Boolean(string='Garage')
    garden = fields.Boolean(string='Garden')
    garden_area = fields.Integer(string='Garden area (sqm)')
    garden_orientation = fields.Selection(
        string='Garden orientation',
        selection=[('north', 'North'), ('south', 'South'), ('east', 'East'), ('west', 'West')])
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection(
        string='Status',
        required=True,
        copy=False,
        default='new',
        selection=[('new', 'New'), ('offer_received', 'Offer received'), ('offer_accepted', 'Offer accepted'),
                   ('sold', 'SOLD'), ('canceled', 'Canceled')])


    def action_sold(self):
        for record in self:
            if record.state == 'canceled':
                raise UserError('Canceled property cannot be marked as sold.')
            record.state = 'sold'


    def action_cancel(self):
        for record in self:
            if record.state == 'sold':
                raise UserError('Sold property cannot be canceled.')
            record.state = 'canceled'

    property_type_id = fields.Many2one(
        'estate.property.type',
        string='Property type',
        required=True,
    )

    salesperson_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        default=lambda self: self.env.user,
    )

    buyer_id = fields.Many2one(
        'res.partner',
        string='Buyer',
        copy=False,
    )

    tag_ids = fields.Many2many(
        'estate.property.tag',
        string='Tags',
    )

    offer_ids = fields.One2many(
        'estate.property.offer',
        'property_id',
        string='Offers',
    )

    total_area = fields.Integer(
        string='Total area (sqm)',
        compute='_compute_total_area',
    )


    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    best_price = fields.Float(
        string='Best offer',
        compute='_compute_best_price',
    )


    @api.depends('offer_ids.price')
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


    _sql_constraints = [
        ('check_expected_price', 'CHECK(expected_price > 0)', 'The expected price must be positive.'),
        ('check_selling_price', 'CHECK(selling_price > 0)', 'The selling price must be positive.')
    ]


    @api.constrains('selling_price', 'expected_price')
    def _check_selling_price(self):
        for record in self:
            if float_is_zero(record.selling_price, precision_digits=2):
                continue
            if float_compare(record.selling_price, 0.9 * record.expected_price, precision_digits=2) < 0:
                raise ValidationError('The selling price cannot be less than 90% of the expected price.')


    @api.ondelete(at_uninstall=False)
    def _check_property_state(self):
        for record in self:
            if record.state not in ['new', 'canceled']:
                raise UserError("You can only delete properties that are in 'New' or 'Canceled' state.")