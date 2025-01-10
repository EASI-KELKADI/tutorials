from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import UserError


class EstatePropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Real estate property offers'
    _rec_name = 'price'
    _order = 'price desc'

    price = fields.Float(string='Price')

    status = fields.Selection(
        string='Status',
        selection=[('accepted', 'Accepted'), ('refused', 'Refused')],
        copy=False,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
    )
    property_id = fields.Many2one(
        'estate.property',
        string='Property',
        required=True,
    )
    # Field to store the validity of the offer in days
    validity = fields.Integer(
        string='Validity (days)',
        default=7,
    )
    # Computed field to store the deadline date
    date_deadline = fields.Date(
        string='Deadline',
        compute='_compute_date_deadline',
        inverse='_inverse_date_deadline',
    )
    # Many2one relation to the property type
    property_type_id = fields.Many2one(
        'estate.property.type',
        string='Property type',
        related='property_id.property_type_id',
        store=True,
        readonly=True)

    # Compute the deadline date based on the creation date and validity
    @api.depends('create_date', 'validity')
    def _compute_date_deadline(self):
        for record in self:
            if record.create_date:
                record.date_deadline = record.create_date + timedelta(days=record.validity)
            else:
                record.date_deadline = fields.Date.today() + timedelta(days=record.validity)

    # Compute the validity based on the creation date and deadline date
    def _inverse_date_deadline(self):
        for record in self:
            if record.create_date and record.date_deadline:
                record.validity = (record.date_deadline - record.create_date.date()).days

    # Method to accept an offer
    def action_accept(self):
        for offer in self:
            accepted_offer = offer.property_id.offer_ids.filtered(lambda o: o.status == 'accepted')
            if accepted_offer:
                raise UserError('This property already has an accepted offer.')
            offer.status = 'accepted'
            offer.property_id.state = 'offer_accepted'
            offer.property_id.selling_price = offer.price
            offer.property_id.buyer_id = offer.partner_id

    # Method to refuse an offer
    def action_refuse(self):
        for offer in self:
            if offer.status == 'accepted':
                raise UserError('You cannot refuse an accepted offer.')
            offer.status = 'refused'

    # Validates and processes the creation of an offer, ensuring that the price is higher than the best offer
    @api.model
    def create(self, vals):
        property_id = vals.get('property_id')
        if not property_id:
            raise UserError('Property ID is missing.')

        property_obj = self.env['estate.property'].browse(property_id)

        best_price = property_obj.best_price
        if vals.get('price') < best_price:
            raise UserError(f'The offer must be higher than {best_price}')

        property_obj.state = 'offer_received'

        return super().create(vals)

    # Ensures that the offer price is positive
    _sql_constraints = [
        ('check_price', 'CHECK(price > 0)', 'The offer price must be positive.')
    ]