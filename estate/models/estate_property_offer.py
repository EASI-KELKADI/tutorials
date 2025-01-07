from datetime import timedelta

from odoo import models, fields, api

class EstatePropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Estate Property Offer'

    price = fields.Float(string='Price', required=True)
    status = fields.Selection([('accepted', 'Accepted'), ('refused', 'Refused')],
    string='Status',
    copy=False)

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    property_id = fields.Many2one('estate.property', string='Property', required=True)

    validity = fields.Integer(string='Validity', default=7)
    date_deadline = fields.Date(
        string='Deadline',
        compute="_compute_date_deadline",
        inverse="_inverse_date_deadline",
        store=True,
    )

    @api.depends('create_date','validity')
    def _compute_date_deadline(self):
        for record in self:
            if record.create_date:
                record.date_deadline = record.create_date + timedelta(days=record.validity)
            else:
                record.date_deadline = None

    def _inverse_date_deadline(self):
        for record in self:
            if record.create_date and record.date_deadline:
                delta = (record.date_deadline - record.create_date.date()).days
                record.validity = delta
            else:
                record.validity = 0

    def action_accept(self):
        for offer in self:
            offer.status = 'accepted'
            offer.property_id.state = 'offer_accepted'
            offer.property_id.buyer_id = offer.partner_id
            offer.property_id.selling_price = offer.price
            other_offers = offer.property_id.offer_ids - offer
            other_offers.write({'status': 'refused'})

    def action_refuse(self):
        for offer in self:
            offer.status = 'refused'