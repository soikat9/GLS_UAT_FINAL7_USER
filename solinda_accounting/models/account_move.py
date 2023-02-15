from itertools import product
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    # @api.model
    # def create(self, vals):
    #     res = super(AccountMove, self).create(vals)
    #     if self.tags_ids:
    #         name_tag = self.tags_ids.mapped('name')
    #         if any('Turn Key' in w for w in name_tag):
    #             res.name = self.env["ir.sequence"].next_by_code("account.move.sequence.turnkey")
    #         elif any('BOO' in w for w in name_tag):
    #             res.name = self.env["ir.sequence"].next_by_code("account.move.sequence.boo")
    #         elif any('OMS' in w for w in name_tag):
    #             res.name = self.env["ir.sequence"].next_by_code("account.move.sequence.oms")
    #         elif any('Trading' in w for w in name_tag):
    #             res.name = self.env["ir.sequence"].next_by_code("account.move.sequence.trading")
    #         else:
    #             pass
    #     return res  

    def view_po_action(self):
        for i in self:
            po_id = i.invoice_line_ids.mapped("purchase_order_id")
            if len(po_id.ids) > 1:
                return{
                    'name': 'Purchase',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'tree,form',
                    'res_model': 'purchase.order',
                    'domain':[('id','in', po_id.ids)],
                    'context': {'create': False},
                }
            else:
                return{
                    'name': 'Purchase',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'purchase.order',
                    'context': {'create': False},
                    'res_id': po_id.id,
                }

    def button_draft(self):
        AccountMoveLine = self.env['account.move.line']
        excluded_move_ids = []

        #menambahkan validation error saat payment state partial
        for move in self:
            if move.payment_state == 'partial':
                raise ValidationError("You must not reset this to Draft because the payment state is Partial")

        if self._context.get('suspense_moves_mode'):
            excluded_move_ids = AccountMoveLine.search(AccountMoveLine._get_suspense_moves_domain() + [('move_id', 'in', self.ids)]).mapped('move_id').ids

        for move in self:
            if move in move.line_ids.mapped('full_reconcile_id.exchange_move_id'):
                raise UserError(_('You cannot reset to draft an exchange difference journal entry.'))
            if move.tax_cash_basis_rec_id or move.tax_cash_basis_origin_move_id:
                # If the reconciliation was undone, move.tax_cash_basis_rec_id will be empty;
                # but we still don't want to allow setting the caba entry to draft
                # (it'll have been reversed automatically, so no manual intervention is required),
                # so we also check tax_cash_basis_origin_move_id, which stays unchanged
                # (we need both, as tax_cash_basis_origin_move_id did not exist in older versions).
                raise UserError(_('You cannot reset to draft a tax cash basis journal entry.'))
            if move.restrict_mode_hash_table and move.state == 'posted' and move.id not in excluded_move_ids:
                raise UserError(_('You cannot modify a posted entry of this journal because it is in strict mode.'))
            # We remove all the analytics entries for this journal
            move.mapped('line_ids.analytic_line_ids').unlink()

        self.mapped('line_ids').remove_move_reconcile()
        self.write({'state': 'draft', 'is_move_sent': False})


    # @api.constrains('ref')
    # def _check_ref_unique(self):
    #     for line in self:
    #         if line.ref:
    #             ref_counts = line.search_count(['|',('ref', '=', line.ref), ('id', '!=', line.id)])
    #             if ref_counts > 0:
    #                 raise ValidationError("Reference number already exists!")

    @api.depends('invoice_line_ids.qty_received_account')
    def _compute_total_qty_received(self):
        for this in self:
            this.total_qty_received = sum(
                this.invoice_line_ids.mapped('qty_received_account'))

    @api.depends('invoice_line_ids.qty_ordered_vendor')
    def _compute_total_qty_ordered(self):
        for this in self:
            this.total_qty_ordered = sum(
                this.invoice_line_ids.mapped('qty_ordered_vendor'))

    @api.depends('invoice_line_ids.detailed_type')
    def _compute_product_type(self):
        label = dict(self._fields['detailed_type'].selection)
        for this in self:
            product = ''
            for lines in this.invoice_line_ids:
                if '%s, ' % label.get(lines.detailed_type) in product:
                    continue
                else:
                    product += '%s, ' % label.get(lines.detailed_type)
            this.product_type = product

    @api.depends('invoice_line_ids.qty_delivered_account')
    def _compute_total_delivered_qty(self):
        for this in self:
            this.total_delivered_qty = sum(
                this.invoice_line_ids.mapped('qty_delivered_account')
            )
    
    @api.depends('invoice_line_ids.qty_ordered_account')
    def _compute_total_qty_sale(self):
        for this in self:
            this.total_qty_sale = sum(
                this.invoice_line_ids.mapped('qty_ordered_account')
            )

    # def _default_transfer(self):
    #     return self.env['account.journal'].search([('name', '=', 'CIMB')], limit=1).id
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True,
        states={'draft': [('readonly', False)]},
        check_company=True, domain="[('id', 'in', suitable_journal_ids)]", default=None)
    total_qty_received = fields.Integer(compute='_compute_total_qty_received', string='Qty Received', store=True)
    total_delivered_qty = fields.Integer(compute='_compute_total_delivered_qty', string='Qty Delivered', store=True)
    total_qty_ordered = fields.Integer(compute='_compute_total_qty_ordered', string='Qty Ordered', store=True)
    total_qty_sale = fields.Integer(compute='_compute_total_qty_sale', string='Qty Ordered', store=True)
    invoice_line_ids = fields.One2many('account.move.line', 'move_id', string='Invoice lines',
                                       copy=False, readonly=True,
                                       domain=[
                                           ('exclude_from_invoice_tab', '=', False)],
                                       states={'draft': [('readonly', False)]})

    product_type = fields.Text(compute='_compute_product_type', string='Product Type')
    detailed_type = fields.Selection([
        ('consu', 'Consumable'),
        ('service', 'Service'),
        ('product', 'Storable Product')], string='Product Type', default='consu', required=True,
        help='A storable product is a product for which you manage stock. The Inventory app has to be installed.\n'
             'A consumable product is a product for which stock is not managed.\n'
             'A service is a non-material product you provide.')  
    approved = fields.Many2one('res.users', string='Approved By')
    transfer = fields.Many2one('account.journal',
        # compute='_default_transfer',
        domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]",
        string='Transfer To Bank'
        )
    tags_ids = fields.Many2many('crm.tag', string='Tags')
    print_button_visible = fields.Char(compute='_compute_print_button_visible', string='Print Button Visible')

    @api.depends('tags_ids')
    def _compute_print_button_visible(self):
        for i in self:
            if i.tags_ids:
                name_tag = i.tags_ids.mapped('name')
                if any('Trading' in w for w in name_tag):
                    i.print_button_visible = 'trading'
                elif any('BOO' in w for w in name_tag):
                    i.print_button_visible = 'boo'
                elif any('OMS' in w for w in name_tag):
                    i.print_button_visible = 'oms'
                elif any('Turn Key' in w for w in name_tag):
                    i.print_button_visible = 'turnkey'
                else:
                    i.print_button_visible = False
            else:
                i.print_button_visible = False

    def action_print_inv_boo(self):
        return self.env.ref('solinda_accounting.report_invoice_boo_action').report_action(self)

    def action_print_inv_oms(self):
        return self.env.ref('solinda_accounting.report_invoice_oms_action').report_action(self)

    def action_print_inv_trading(self):
        return self.env.ref('solinda_accounting.report_invoice_trading_action').report_action(self)
    
    def action_print_inv_turnkey(self):
        return self.env.ref('solinda_accounting.report_invoice_turnkey_action').report_action(self)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    purchase_line_id = fields.Many2one(
        'purchase.order.line', 'Purchase Order Line', ondelete='set null', index=True)
    qty_received_account = fields.Float(related='purchase_line_id.qty_received', store=True, string="Qty Received")
    qty_ordered_vendor = fields.Float(related='purchase_line_id.product_qty', store=True, string="Qty Ordered")
    product_id = fields.Many2one(
        'product.product', string='Product', ondelete='restrict')
    detailed_type = fields.Selection(related='product_id.detailed_type', string='Product Type')
    qty_delivered_account = fields.Float(string='Qty Delivered', store=True)
    qty_ordered_account = fields.Float(string='Qty Ordered', store=True)
    account_group_id = fields.Many2one('account.analytic.group', string='Account Group', related='analytic_account_id.group_id', store=True)

    # @api.onchange('analytic_account_id')
    # def _onchange_analytic_account_id(self):
    #     for i in self:
    #         if i.analytic_account_id:
    #             i.account_group_id = i.analytic_account_id.group_id.id

    @api.depends('sale_order_line')
    def _compute_delivered(self):
        if self.sale_order_line:
            self.qty_delivered_account = self.sale_order_line.qty_delivered
            self.qty_ordered_account = self.sale_order_line.product_uom_qty