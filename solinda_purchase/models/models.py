# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    name_project = fields.Char(string='Name Project')
    need_category = fields.Selection([
        ('project', 'Project'),
        ('operational', 'Operational'),
        ('maintenance', 'Maintenance'),
        ('trading', 'Trading'),
        ('bidding', 'Bidding')
    ], string='Need Category')
    ordering_date = fields.Date(string="Ordering Date", tracking=True,default=fields.Date.today)
    date_end = fields.Date(string='Deadline', tracking=True)
    date_total = fields.Integer(string='Total Date', compute='check_date_deadline')
    btn_hide_req = fields.Boolean(string='Hide', default=True)
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('purchase.requisition.req')
        return super(PurchaseRequisition, self).create(vals)
    
    def check_date_deadline(self):
        for rec in self:
            if rec.date_end and rec.ordering_date:
                rec.date_total = (rec.date_end - rec.ordering_date).days
                if rec.date_total < 3:
                    raise ValidationError("Date Deadline must be at least 3 days after the Create Date")

class DeliveryLocation(models.Model):
    _name = 'delivery.location'
    _description = 'Delivery Location'

    name = fields.Char(string='Delivery Location')

class PurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'

    merk_recommended = fields.Char(string='Merk Recommended')
    price_target = fields.Float('Price Target')
    date_plan_required = fields.Date('Date Plan Required')
    delivery_location_id = fields.Many2one(string='Delivery Location', comodel_name='delivery.location', ondelete='restrict')
    product_description_variants = fields.Text(string='Custom Description', readonly=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            product_description_variants = ''
            # if self.product_id.code:
            #     product_description_variants = "[{}] {}".format(self.product_id.default_code, product_description_variants)
            if self.product_id.type_pur:
                product_description_variants += "type : " + self.product_id.type_pur + ";"
            if self.product_id.debit:
                product_description_variants += "\n" + "debit : " + self.product_id.debit + ";"
            if self.product_id.head:
                product_description_variants += "\n" + "head : " + self.product_id.head + ";"
            if self.product_id.voltage:
                product_description_variants += "\n" + "voltage : " + self.product_id.voltage + ";"
            if self.product_id.casing:
                product_description_variants += "\n" + "material casing : " + self.product_id.casing + ";"
            if self.product_id.impeller:
                product_description_variants += "\n" + "material impeller : " + self.product_id.impeller + ";"
            self.product_uom_id = self.product_id.uom_id.id
            self.product_description_variants = product_description_variants

class ProductProduct(models.Model):
    _inherit = 'product.product'

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    type_pur = fields.Char(string='Type')
    debit = fields.Char(string='Debit')
    head = fields.Char(string='Head')
    voltage = fields.Char(string='Voltage')
    casing = fields.Char(string='Casing')
    impeller = fields.Char(string='Impeller')

class PurchaseOrderLine(models.Model):
    _inherit ='purchase.order.line'

    project_code_po = fields.Char(string='Project Code', store=True)

class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    reviewed = fields.Many2one('res.users', string='Reviewed By')
    approved = fields.Many2one('res.users', string='Approved By')
    best_regard = fields.Many2one('res.users', string='Requested By')

    def _purchase_request(self, sequence=False):
        res = super(PurchaseRequest, self)._purchase_request()
        res.update({
            'project_code_po': self.project_code
            })
        return res

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    name = fields.Char(string='Order Reference')
    notes = fields.Html(string='Notes')
    courier = fields.Char('Courier')
    location_id = fields.Many2one('stock.location', string='Location',store=True)
    field_loc = fields.Boolean(string='Field Location', default=False)

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('submit', 'Submitted'),
        ('select', 'Selected'),
        ('confirm', 'Confirmed'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    # currency_id = fields.Many2one('res.currency', 'Currency', required=True, states=READONLY_STATES, related="partner_id.property_purchase_currency_id")
    prepared = fields.Many2one('res.users', string='Prepared By')
    verified = fields.Many2one('res.users', string='Verified By')
    approved = fields.Many2one('res.users', string='Approved By')
    received = fields.Char(string='Received By')
    best_regard = fields.Many2one('res.users', string='Best Regards By')
    so_trading_id = fields.Many2one('sale.order', string="SO Trading")
    btn_hide = fields.Boolean(string='Hide', default=False)

    def _get_destination_location(self):
        self.ensure_one()
        if self.location_id:
            return self.location_id.id
        if self.dest_address_id:
            return self.dest_address_id.property_stock_customer.id
        return self.picking_type_id.default_location_dest_id.id


    @api.onchange('requisition_id')
    def _onchange_requisition_id(self):
        if not self.requisition_id:
            return

        self = self.with_company(self.company_id)
        requisition = self.requisition_id
        if self.partner_id:
            partner = self.partner_id
        else:
            partner = requisition.vendor_id
        payment_term = partner.property_supplier_payment_term_id

        FiscalPosition = self.env['account.fiscal.position']
        fpos = FiscalPosition.with_company(self.company_id).get_fiscal_position(partner.id)

        self.partner_id = partner.id
        self.fiscal_position_id = fpos.id
        self.payment_term_id = payment_term.id,
        self.company_id = requisition.company_id.id
        self.currency_id = requisition.currency_id.id
        if not self.origin or requisition.name not in self.origin.split(', '):
            if self.origin:
                if requisition.name:
                    self.origin = self.origin + ', ' + requisition.name
            else:
                self.origin = requisition.name
        self.notes = requisition.description
        self.date_order = fields.Datetime.now()
        self.btn_hide = requisition.btn_hide_req

        if requisition.type_id.line_copy != 'copy':
            return

        # Create PO lines if necessary
        order_lines = []
        for line in requisition.line_ids:
            # Compute name
            product_lang = line.product_id.with_context(
                lang=partner.lang or self.env.user.lang,
                partner_id=partner.id
            )
            name = product_lang.display_name
            if product_lang.description_purchase:
                name += '\n' + product_lang.description_purchase

            # Compute taxes
            taxes_ids = fpos.map_tax(line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id)).ids

            # Compute quantity and price_unit
            if line.product_uom_id != line.product_id.uom_po_id:
                product_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_po_id)
                price_unit = line.product_uom_id._compute_price(line.price_unit, line.product_id.uom_po_id)
            else:
                product_qty = line.product_qty
                price_unit = line.price_unit

            if requisition.type_id.quantity_copy != 'copy':
                product_qty = 0

            # Create PO line
            order_line_values = line._prepare_purchase_order_line(
                name=name, product_qty=product_qty, price_unit=price_unit,
                taxes_ids=taxes_ids)
            order_lines.append((0, 0, order_line_values))
        self.order_line = order_lines


    @api.onchange('partner_id')
    def _onchange_partner_id_change_currency(self):
        for i in self:
            if i.partner_id:
                i.currency_id = i.partner_id.property_purchase_currency_id
            else:
                i.currency_id = False


    @api.depends('date_order', 'currency_id', 'company_id', 'company_id.currency_id')
    def _compute_currency_rate(self):
        for order in self:
            if order.currency_id == order.company_id.currency_id:
                order.currency_rate = 0
            else:
                order.currency_rate = self.env['res.currency']._get_conversion_rate(order.company_id.currency_id, order.currency_id, order.company_id, order.date_order)


    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent','confirm']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

    def submit_purchase(self):
        # Purchasing Staff
        self.write({'state': 'submit'})

    def confirm_purchase(self):
        # Procurement Manager
        self.write({'state': 'confirm'})

    def rfq_selected(self):
        # special from requisition
        if self.requisition_id:
            request = self.env["purchase.order"].search([("requisition_id", "=", self.requisition_id.id)])
            for r in request:
                if r.id != self.id:
                    r.button_cancel()
                else:
                    r.state = 'select'

    @api.model
    def create(self, vals):
        if vals.get('requisition_id'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pur.order.from.requisition')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order.req')
        return super(PurchaseOrder, self).create(vals)

    @api.model
    def _prepare_picking(self):
        vals = super(PurchaseOrder, self)._prepare_picking()
        vals.update({
            'location_dest_id': self.location_id.id
            })
        return vals