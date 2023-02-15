import copy
import email
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round

class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    rab_id = fields.Many2one('cost.sheet', string='Cost Sheet')    
    rap_id = fields.Many2one('rap.rap', string='Cost Sheet')    

class CostSheet(models.Model):
    _name = 'cost.sheet'
    _description = 'Cost Sheet'
    _inherit = ['portal.mixin','mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Name',tracking=True)
    crm_id = fields.Many2one('crm.lead', string='CRM',required=True,tracking=True,copy=True)
    partner_id = fields.Many2one('res.partner', string='Customer',tracking=True,copy=True,required=True)
    date_document = fields.Date('Request Date',tracking=True,default=fields.Date.today,copy=True)
    user_id = fields.Many2one('res.users', string='Responsible',tracking=True,default=lambda self:self.env.user.id,copy=True)
    # rab_template_id = fields.Many2one('rab.template', string='RAB Template',tracking=True,copy=True)
    note = fields.Text('Terms and condition',copy=True,tracking=True)
    tax_ids = fields.Many2many('account.tax', string='Taxs',copy=True)
    tax_id = fields.Many2one('account.tax', string='Tax',copy=True)
    rev = fields.Integer('Revision')
    revisied = fields.Boolean('Revisied')
    cost_sheet_revision_id = fields.Many2one('cost.sheet', string='Cost Sheet Revision')
    tax_id = fields.Many2one('account.tax', string='Tax',copy=True)
    item_line_ids = fields.One2many('item.item', 'cost_sheet_id', string='Items Line',copy=True)
    component_line_ids = fields.One2many('component.component', 'cost_sheet_id', string='Component Line',copy=True)
    category_line_ids = fields.One2many('rab.category', 'cost_sheet_id', string='Category Line',copy=True)
    ga_project_line_ids = fields.One2many('ga.project', 'cost_sheet_id', string='GA Project Line',copy=True)
    waranty_line_ids = fields.One2many('waranty.waranty', 'cost_sheet_id', string='Waranty Line',copy=True)
    project_id = fields.Many2one('project.project')
    
    @api.onchange('category_line_ids')
    def _onchange_line(self) :
        for line in self.category_line_ids :
            line._compute_sequence_categ()
    
    subtotal = fields.Float(compute='_compute_subtotal', string='Subtotal',store=True,copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submited'),
        ('approved', 'Approved'),
        ('reject', 'Rejected'),
    ], string='Status',tracking=True, default="draft",copy=False)
    
    currency_id = fields.Many2one('res.currency',default=lambda self:self.env.company.currency_id.id)
    ga_project = fields.Float('GA Project',compute="_compute_ga_project",store=True,copy=False)
    ga_project_percent = fields.Float('GA Project Percent',compute="_compute_ga_project",store=True,copy=False)
    project_hse = fields.Float('Project HSE',compute="_compute_project_hse",store=True,copy=False)
    project_hse_percent = fields.Float('Project HSE Percent',copy=True)
    car = fields.Float('Construction All Risk',compute="_compute_car",store=True,copy=False)
    car_percent = fields.Float('CAR Percent',copy=True)
    financial_cost = fields.Float('Financial Cost During Construction',copy=True)
    financial_cost_percent = fields.Float('Financial Cost Percent',compute="_compute_fin_cost_percent",store=True,copy=False)
    bank_guarantee = fields.Float('Bank Guarantee',copy=True)
    bank_guarantee_percent = fields.Float('Bank Guarantee percent',compute="_compute_bank_guarantee_percent",store=True,copy=False)
    contigency = fields.Float('Contigency',compute="_compute_contigency",store=True,copy=False)
    contigency_percent = fields.Float('Contigency Percent',copy=True)
    other_price = fields.Float('Other')
    waranty = fields.Float('Warranty',compute="_compute_waranty",store=True,copy=False)
    waranty_percent = fields.Float('Warranty Percent',copy=True)
    
    pph = fields.Float('PPh',copy=True)
    
    subtotal_non_project = fields.Float(compute='_compute_subtotal_non_project', string='Subtotal Non Project',store=True,copy=False)
    project_value = fields.Float(compute='_compute_project_value', string='Project Cost',store=True,copy=False)
    profit = fields.Float(compute='_compute_profit', string='Profit',store=True,copy=False)
    profit_propotional = fields.Float('Profit %')
    sales = fields.Float(compute='_compute_sales', string='Project Cost + Profit',store=True,copy=False)
    offer_margin = fields.Float(compute='_compute_offer_margin', string='Offer Margin',store=True,copy=False)
    offer_margin_percentage = fields.Float('Offer Margin %')
    total_cost_with_margin = fields.Float('Total Cost + Offer Margin',compute="_compute_total_amount",store=True,copy=False)
    total_cost_round_up = fields.Float('Sales (Round Up)',compute="_compute_total_amount",store=True,copy=False)
    
    pph_percent = fields.Float('PPh %',compute="_compute_total_amount",store=True,copy=False)
    final_profit = fields.Float('Final Profit',compute="_compute_total_amount",store=True,copy=False)
    final_profit_percent = fields.Float('Final Profit %',compute="_compute_total_amount",store=True,copy=False)
    taxes = fields.Float('VAT',compute="_compute_total_amount",store=True,copy=False)
    total_amount = fields.Float(compute='_compute_total_amount', string='Total Amount',store=True,copy=False)
    
    # Other Information
    subject = fields.Char(copy=True)
    attn_id = fields.Many2one('res.partner', string='Attn', related='partner_id')
    to = fields.Char(related='attn_id.parent_id.name', string='To')
    attn = fields.Char(related='attn_id.name', string='Attn')    
    phone = fields.Char(related='attn_id.phone', store=True,copy=False)
    email = fields.Char(related='attn_id.email', store=True,copy=False)
    ref_turnkey = fields.Char(string='Ref',copy=True)
    approved_by_id = fields.Many2one('res.users', string='Approved By',tracking=True,copy=True)
    # Terms and Conditions
    quotation_validity = fields.Char('Quotation Validity',copy=True)
    delivery_time = fields.Char('Delivery Time',copy=True)
    delivery_point = fields.Char('Delivery Point',copy=True)
    toc_price = fields.Html('Price',copy=True)
    payment_terms = fields.Html('Payment Terms',copy=True)
    project_code = fields.Char('Project Code', related="crm_id.project_code")
    best_regardx = fields.Many2one('res.users', string='Best Regards',copy=True)
    approved_byx = fields.Many2one('res.users', string='Approved By',copy=True)
    received_byx = fields.Many2one('res.users', string='Received By',copy=True)
    best_regard = fields.Many2one('res.users', string='Best Regards',copy=True)
    approved_by = fields.Many2one('res.users', string='Approved By',copy=True)
    received_by = fields.Many2one('res.users', string='Received By',copy=True)
    requisition_id = fields.Many2one('purchase.requisition', string='Requisition',copy=True)

    def action_print_quotation(self):
        return self.env.ref('sol_cost_sheet.report_quotation_turnkey_action').report_action(self)
    
    def action_print_quotation_trading(self):
        return self.env.ref('sol_cost_sheet.report_quotation_trading_action').report_action(self)
    
    @api.model
    def create(self, vals):
        res = super().create(vals)
        if not res.revisied:
            res.name = self.env["ir.sequence"].next_by_code("cost.sheet.seq")
        res.crm_id.rab_id = res.id
        return res 
    
    def create_revision(self):
        new_name = self.name[0: self.name.index(' Rev.')] if self.revisied else self.name
        cost_sheet = self.copy(
            {
            'name': "%s Rev. %s"%(new_name,self.rev + 1),
            'rev': self.rev + 1,
            'cost_sheet_revision_id' : self.id,
            'revisied': True,
        }
        )
        for category in cost_sheet.category_line_ids:
            category.parent_component_line_ids.write({'cost_sheet_id': cost_sheet.id})
            for component in category.parent_component_line_ids:
                for item in component.item_ids:
                    item.write({
                        'cost_sheet_id': item.component_id.cost_sheet_id.id,
                        'category_id': item.component_id.category_id.id,
                    })
        cost_sheet.recompute()
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "cost.sheet",
            "res_id": cost_sheet.id
        }
    
    
    def action_view_crm(self):
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "crm.lead",
            "res_id": self.crm_id.id
        }

    def action_purchase_requisition(self):
        if not self.requisition_id:
            ir = self.env['purchase.requisition'].create({'user_id':self.env.user.id})
            ir.update({
                'name_project': self.crm_id.name,
            })
            if ir:
                self.requisition_id = ir.id
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "purchase.requisition",
            # "domain": [("rab_id", "=", self.id)],
            "context": {'default_rab_id':self.id},
            "res_id": self.requisition_id.id
        }
        
    def action_submit(self):
        self.write({'state':'submit'})
    def action_done(self):
        self.write({'state':'approved','approved_by_id':self.env.user.id})
    def action_reject(self):
        self.write({'state':'reject'})
    def action_to_draft(self):
        self.write({'state':'draft'})
    
    
    @api.depends('offer_margin_percentage','offer_margin','sales','project_value','tax_id','pph')
    def _compute_total_amount(self):
        for this in self:
            total_cost = 0.0
            round_up = 0.0
            final_profit = 0.0
            final_profit_percent = 0.0
            taxes = 0.0
            total_amount = 0.0
            
            total_cost = this.offer_margin + this.sales
            round_up = float_round(total_cost,precision_digits=-6,rounding_method='UP') if total_cost > 0 else 0.0
            final_profit = round_up - this.project_value - this.pph
            final_profit_percent = final_profit/round_up if this.project_value >0 and round_up >0 else 0.0
            taxes = round_up * (this.tax_id.amount/100)
            total_amount = round_up + taxes
            pph = this.pph / round_up if this.pph and round_up else 0.0
            
            
            this.total_cost_with_margin = total_cost
            this.total_cost_round_up = round_up
            this.final_profit = final_profit
            this.pph_percent = pph
            this.final_profit_percent = final_profit_percent
            this.taxes = taxes
            this.total_amount = total_amount
    
    
    @api.depends('offer_margin_percentage','sales')
    def _compute_offer_margin(self):
        for this in self:
            this.offer_margin = this.offer_margin_percentage * this.sales
    
        
    @api.depends('profit_propotional','project_value')
    def _compute_sales(self):
        for this in self:
            this.sales = this.project_value / (1 - this.profit_propotional)
    
    @api.depends('sales','project_value','category_line_ids.price','category_line_ids.final_price_percentage','project_value','sales')
    def _compute_profit(self):
        for this in self:
            this.profit =  this.sales - this.project_value
    
    @api.depends('subtotal','subtotal_non_project')
    def _compute_project_value(self):
        for this in self:
            this.project_value = this.subtotal + this.subtotal_non_project
    
    
    @api.depends('ga_project','project_hse','car','financial_cost','bank_guarantee','contigency','waranty','other_price')
    def _compute_subtotal_non_project(self):
        for this in self:
            this.subtotal_non_project = sum([this.ga_project,this.project_hse,this.car,this.financial_cost,this.bank_guarantee,this.contigency,this.waranty,this.other_price])
    
        
    @api.depends('ga_project_line_ids.total_price')
    def _compute_ga_project(self):
        for this in self:
            this.ga_project = sum(this.ga_project_line_ids.mapped('total_price'))
            this.ga_project_percent = this.ga_project / this.project_value if this.project_value > 0 else 0.0
    
    @api.depends('ga_project','project_hse_percent')
    def _compute_project_hse(self):
        for this in self:
            this.project_hse = this.ga_project * this.project_hse_percent
            
    @api.depends('subtotal','car_percent')
    def _compute_car(self):
        for this in self:
            this.car = this.subtotal * this.car_percent
            
    @api.depends('project_value','financial_cost')
    def _compute_fin_cost_percent(self):
        for this in self:
            this.financial_cost_percent = this.financial_cost / this.project_value if this.financial_cost >0 and this.project_value > 0 else 0.0
    @api.depends('project_value','bank_guarantee')
    def _compute_bank_guarantee_percent(self):
        for this in self:
            this.bank_guarantee_percent = this.bank_guarantee / this.project_value if this.bank_guarantee >0 and this.project_value > 0 else 0.0

    @api.depends('subtotal','contigency_percent')
    def _compute_contigency(self):
        for this in self:
            this.contigency = this.subtotal * this.contigency_percent
            
    
    @api.depends('waranty_line_ids.total_price','project_value')
    def _compute_waranty(self):
        for this in self:
            this.waranty = sum(this.waranty_line_ids.mapped('total_price'))
            this.waranty_percent = this.waranty / this.project_value if this.project_value > 0 else 0.0
        
    @api.depends('category_line_ids.price')
    def _compute_subtotal(self):
        for this in self:
            this.subtotal = sum(this.category_line_ids.mapped('price'))


class RabCategory(models.Model):
    _name = 'rab.category'
    _description = 'Rab Category'
    _rec_name = 'product_id'
    _order = "sequence"

    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet',ondelete="cascade")
    product_id = fields.Many2one('product.product',required=False)

    parent_component_line_ids = fields.One2many('component.component', 'category_id', string='Parent Component Line',copy=True)
    sequence = fields.Integer('Sequence')
    price = fields.Float(compute='_compute_price',store=True)
    propotional = fields.Float(compute='_compute_price', string='Propotional',store=True)
    suggested_proposional = fields.Float(compute='_compute_sug_price', string='Sug. Commercial Price',store=True)
    input_manual = fields.Boolean('Adjust Manual')
    final_price  = fields.Float('Final Price',compute="_compute_final_price",inverse="_inverse_final_price")
    final_price_percentage = fields.Float('Final %')
    state_rab = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submited'),
        ('approved', 'Approved'),
        ('reject', 'Rejected'),
    ], string='Status',related='cost_sheet_id.state')

    # sequence_categ = fields.Integer(compute='_compute_sequence_categ', string='Sequence')
    sequence_categ = fields.Integer(string='Sequence')
    total_qty = fields.Integer(compute='_compute_total_qty', string='Total Quantity')
    
    # @api.depends('sequence')
    # def _compute_sequence_categ(self):
    #     for i in self:
    #         i.sequence_categ = i.sequence + 1
    # @api.depends('sequence')
    
    @api.onchange('sequence')
    def _compute_sequence_categ(self):
        for i in self:
            line = i.cost_sheet_id.category_line_ids
            totseq = sum(line.mapped('sequence'))
            if totseq == 0:
                seq = 1
                for l in line:
                    l.sequence_categ = seq
                    seq += 1
            else:
                i.sequence_categ = i.sequence +1
                # i.sequence_categ = len(line.ids)+1

    @api.depends('parent_component_line_ids','parent_component_line_ids.product_qty')
    def _compute_total_qty(self):
        for i in self:
            n = []
            n = [q.product_qty for q in i.parent_component_line_ids]
            i.total_qty = sum(n)


    
    def name_get(self):
        return [(i.id, "[%s] %s" % (i.cost_sheet_id.name,i.product_id.display_name)) for i in self]
    
    @api.depends('cost_sheet_id.total_cost_round_up','input_manual','price','final_price_percentage')
    def _compute_final_price(self):
        for this in self:
            amount = 0.0
            total_amount = 0.0
            total_input_amount = 0.0
            if this.cost_sheet_id.total_cost_round_up > 0 :
                if this.input_manual:
                    percent = sum(this.cost_sheet_id.category_line_ids.mapped('final_price_percentage')) - this.final_price_percentage
                    diff_percent = 1 - percent if percent < 1 else percent-1
                    this.final_price =  this.cost_sheet_id.total_cost_round_up * diff_percent
                    this.write({'final_price_percentage': diff_percent})
                else:
                    amount = this.final_price_percentage * this.cost_sheet_id.total_cost_round_up
                    total_amount = float_round(amount,precision_digits=-5,rounding_method='UP')
                    this.final_price =  total_amount
                    
            else:
                this.final_price = 0.0
                this.final_price_percentage = 0.0
                
    
    def _inverse_final_price(self):
        for this in self:
            amount = 0.0
            total_amount = 0.0
            total_input_amount = 0.0
            if this.input_manual:
                percent = sum(this.cost_sheet_id.category_line_ids.mapped('final_price_percentage')) - this.final_price_percentage
                diff_percent = 1 - percent if percent < 1 else percent-1
                this.final_price =  this.cost_sheet_id.total_cost_round_up * diff_percent
                this.write({'final_price_percentage': diff_percent})
            else:
                amount = this.final_price_percentage * this.cost_sheet_id.total_cost_round_up
                total_amount = float_round(amount,precision_digits=-5,rounding_method='UP')
                this.final_price =  total_amount
                
    
    
    
    @api.depends('price','propotional','cost_sheet_id.subtotal_non_project','cost_sheet_id.pph','cost_sheet_id.final_profit')
    def _compute_sug_price(self):
        for this in self:
            this.suggested_proposional = this.price + this.propotional * (this.cost_sheet_id.final_profit + this.cost_sheet_id.subtotal_non_project + this.cost_sheet_id.pph)
            
    
    
    @api.depends('parent_component_line_ids.total_price','cost_sheet_id.subtotal')
    def _compute_price(self):
        for this in self:
            price = 0
            propotional = 0
            
            price = sum(this.parent_component_line_ids.mapped('total_price'))
            propotional = price / this.cost_sheet_id.subtotal if this.cost_sheet_id.subtotal else 0.0
            
            this.price = price
            this.propotional = propotional
    

    
    @api.constrains('product_id')
    def _constrains_product_id(self):
        for this in self:
            data = this.env['rab.category'].search([('cost_sheet_id', '=', this.cost_sheet_id.id),('product_id', '=', this.product_id.id)])
            if len(data) > 1:
                raise ValidationError('Cannot create same product in one cost sheet')
            
    
    def action_view_detail(self):
        return {
                'name': 'Component RAB',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'rab.category',
                'target':'new',
                'res_id': self.id,
            }

class GaProject(models.Model):
    _name = 'ga.project'
    _description = 'Ga Project'
    
    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet',ondelete="cascade")
    rap_id = fields.Many2one('rap.rap', string='Cost Sheet',ondelete="cascade")
    product_id = fields.Many2one('product.product',required=True)    
    product_qty = fields.Integer('Quantity')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id')
    existing_price = fields.Float('Existing Price')
    rfq_price = fields.Float('RFQ Price', store=True)
    total_price = fields.Float(compute='_compute_total_price', string='Total Price',store=True)
    rap_price = fields.Float('RAP Total Price')
    remarks = fields.Text('Remarks')
    realization_price = fields.Float(compute='_compute_realization_price', string='Realization Price')
    
    @api.depends('product_id')
    def _compute_realization_price(self):
        for i in self:
            if i.product_id:
                data = sum(i.env['account.move.line'].search([('product_id', '=', i.product_id.id),('move_id.state', '=', 'posted'),('move_id.purchase_id.project_code', '=', i.rap_id.project_code)]).mapped('price_subtotal'))
                i.realization_price = data
            else:
                i.realization_price = 0
    
    @api.depends('product_qty','rfq_price')
    def _compute_total_price(self):
        for this in self:
            this.total_price = this.product_qty * this.rfq_price
    
    @api.onchange('product_id')
    def _onchange_existing(self):
        if self.product_id:
            existing_price = ''
            if self.product_id.last_purchase_price:
                existing_price = self.product_id.last_purchase_price
            self.existing_price = existing_price
    
    @api.onchange('product_id')
    def _onchange_rfq_price(self):
        if self.product_id:
            rfq_price = ''
            if self.product_id.last_purchase_price:
                rfq_price = self.product_id.last_purchase_price
            self.rfq_price = rfq_price
    

class WarantyWaranty(models.Model):
    _name = 'waranty.waranty'
    _description = 'Waranty'
    
    cost_sheet_id = fields.Many2one('cost.sheet', string='Cost Sheet',ondelete="cascade")
    rap_id = fields.Many2one('rap.rap', string='Cost Sheet',ondelete="cascade")
    
    product_id = fields.Many2one('product.product',required=True)    
    product_qty = fields.Integer('Quantity')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id')
    existing_price = fields.Float('Existing Price')
    rfq_price = fields.Float('RFQ Price', store=True)
    total_price = fields.Float(compute='_compute_total_price', string='Total Price',store=True)
    remarks = fields.Text('Remarks')
    rap_price = fields.Float('RAP Price')
    realization_price = fields.Float(compute='_compute_realization_price', string='Realization Price')
    po_price = fields.Float( string='Po Price')
    analytic_account_id = fields.Many2one(comodel_name="account.analytic.account",string="Analytic Account",tracking=True)

    # po_price = fields.Float(compute='_compute_po_price', string='Po Price')
    
    # @api.depends('product_id','rap_id')
    # def _compute_po_price(self):
    #     for i in self:
    #         if i.product_id:
    #             pol = i.env['purchase.order.line'].search([('product_id', '=', i.product_id.id),('project_code', '=', i.rap_id.project_code)]).mapped('price_subtotal')
    #             if pol:
    #                 i.realization_price = sum(pol)
    #             else:
    #                 i.realization_price = 0
    #         else:
    #             i.realization_price = 0


    @api.depends('product_id','analytic_account_id')
    def _compute_realization_price(self):
        for i in self:
            if i.product_id:
                # data = sum(i.env['account.move.line'].search([('product_id', '=', i.product_id.id)]).mapped('price_subtotal'))
                # data = sum(i.env['account.move.line'].search([('product_id', '=', i.product_id.id),('move_id.state', '=', 'posted'),('move_id.purchase_id.project_code', '=', i.rap_id.project_code)]).mapped('price_subtotal'))
                data = sum(i.env['account.move.line'].search([('product_id', '=', i.product_id.id),('move_id.state', '=', 'posted'),('analytic_account_id', '=', i.analytic_account_id.id)]).mapped('price_subtotal'))
                i.realization_price = data
            else:
                i.realization_price = 0
    
    @api.depends('product_qty','rfq_price')
    def _compute_total_price(self):
        for this in self:
            this.total_price = this.product_qty * this.rfq_price
    
    @api.onchange('product_id')
    def _onchange_existing(self):
        if self.product_id:
            existing_price = ''
            if self.product_id.last_purchase_price:
                existing_price = self.product_id.last_purchase_price
            self.existing_price = existing_price

    @api.onchange('product_id')
    def _onchange_rfq_price(self):
        if self.product_id:
            rfq_price = ''
            if self.product_id.last_purchase_price:
                rfq_price = self.product_id.last_purchase_price
            self.rfq_price = rfq_price