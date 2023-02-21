# -*- coding: utf-8 -*-
import logging
import time
import tempfile
import binascii
import xlrd
import io
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from odoo.exceptions import Warning, UserError
from odoo import models, fields, exceptions, api, _

_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    _description = 'Inherited Purchase Order'

    custom_sequence = fields.Boolean('Custom Sequence')
    system_sequence = fields.Boolean('System Sequence')


class ImportPurchaseOrder(models.TransientModel):
    _name = "import.purchase.order"
    _description = 'Import Purchase Order'

    file = fields.Binary('Upload File')
    purchase_sequence_opt = fields.Selection(
        [('custom', 'Use Excel/CSV Sequence Number'), ('system', 'Use System Default Sequence Number')],
        string='Sequence Available', default='custom')
    purchase_import_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='File Type', default='xls')
    purchase_stage = fields.Selection(
        [('draft', 'Import Quotation in Draft Stage'), ('confirm', 'Confirm Quotation Automatically while Importing')],
        string="Quotation State Available", default='confirm')
    import_product_search = fields.Selection([('by_code', 'Search By Code'), ('by_name', 'Search By Name'), ('by_ids', 'Search By ID')],
                                             string='Product Search Option', default='by_name')

    def make_purchase_order(self, values):
        purchase_obj = self.env['purchase.order']
        purchase_search = purchase_obj.search([
            ('name', '=', values.get('ref'))
        ])
        if purchase_search:
            # if sale_search.payment_term_id.name == values.get('payment'):
            if purchase_search.partner_id.name == values.get('vendor'):
                if purchase_search.currency_id.name == values.get('currency'):
                    lines = self.make_purchase_order_line(values, purchase_search)
                    return purchase_search
                else:
                    raise Warning(
                        _('Pricelist is different for "%s" .\n Please define same.') % values.get('ref'))
            else:
                raise Warning(
                    _('Customer name is different for "%s" .\n Please define same.') % values.get('ref'))
        else:
            if values.get('seq_opt') == 'system':
                name = self.env['ir.sequence'].next_by_code('purchase.order')
            elif values.get('seq_opt') == 'custom':
                name = values.get('ref')
            partner_id = self.search_partner(values.get('vendor'))
            user_id = self.search_user(values.get('user'))
            currency_id = self.search_currency(values.get('currency'))
            order_date = self.make_order_date(values.get('date'))
            # deliver_id = self.search_deliver(values.get('deliver'))
            location_id = self.search_location(values.get('location'))
            payment_id = self.search_payment_terms(values.get('payment'))
            code = values.get('code')
            # approve_date = self.make_deliv_date(values.get('approve_date'))

            purchase_id = purchase_obj.create({
                'partner_id': partner_id.id,
                'name': name,
                'user_id': user_id.id,
                'currency_id': currency_id.id,
                # 'picking_type_id': deliver_id.id,
                'location_id': location_id.id,
                'payment_term_id': payment_id.id,
                'project_code': code,
                'date_order': order_date,
                # 'date_approve': approve_date,
                'field_loc': True,
                'custom_sequence': True if values.get('seq_opt') == 'custom' else False,
                'system_sequence': True if values.get('seq_opt') == 'system' else False,
            })
            lines = self.make_purchase_order_line(values, purchase_id)
            return purchase_id

    def make_purchase_order_line(self, values, purchase_id):
        product_obj = self.env['product.product']
        order_line_obj = self.env['purchase.order.line']
        product_uom = self.env['uom.uom'].search([('name', '=', values.get('uom'))])
        account_analytic_id = self.env['account.analytic.account'].search([('name', '=', values.get('analytic'))])
        tax_ids = []
        product_id = ''
        # Search By Product
        try:
            if self.import_product_search == 'by_code':
                product_id = product_obj.search([('default_code', '=', values.get('product'))])
            elif self.import_product_search == 'by_name':
                product_id = product_obj.search([('name', '=', values.get('product'))])
            elif self.import_product_search == 'by_ids':
                product_id = product_obj.search([('id', '=', values.get('product'))])
            if not product_id:
                product_id = product_obj.create({'name': values.get('product')})

        except Exception:
            raise UserError(_("Product not present. For creating new product please provide product name"))
        if values.get('tax'):
            if ';' in values.get('tax'):
                tax_names = values.get('tax').split(';')
                for name in tax_names:
                    tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
                    if not tax:
                        raise Warning(_('"%s" Tax not present in your system') % name)
                    tax_ids.append(tax.id)

            elif ',' in values.get('tax'):
                tax_names = values.get('tax').split(',')
                for name in tax_names:
                    tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
                    if not tax:
                        raise Warning(_('"%s" Tax not present in your system') % name)
                    tax_ids.append(tax.id)
            else:
                tax_names = values.get('tax')
                tax = self.env['account.tax'].search([('name', '=', tax_names), ('type_tax_use', '=', 'purchase')])
                if not tax:
                    raise Warning(_('"%s" Tax not present in your system') % tax_names)
                tax_ids.append(tax.id)

        if not product_uom:
            raise Warning(_(' "%s" Product UOM category is not present.') % values.get('uom'))
        if not account_analytic_id:
            raise Warning(_(' "%s" Account Analytic category is not present.') % values.get('analytic'))

        res = order_line_obj.create({
            'product_id': product_id.id,
            'product_qty': values.get('quantity'),
            'price_unit': values.get('price'),
            # 'name': values.get('description'),
            'product_uom': product_uom.id,
            'account_analytic_id': account_analytic_id.id, 
            'order_id': purchase_id.id,
            'discount': values.get('discount')

        })
        if tax_ids:
            res.write({'taxes_id': ([(6, 0, tax_ids)])})
        return True

    def make_order_date(self, date):
        DATETIME_FORMAT = "%Y-%m-%d"
        i_date = datetime.strptime(str(date), DATETIME_FORMAT)
        return i_date

    def search_user(self, name):
        user_obj = self.env['res.users']
        user_search = user_obj.search([('name', '=', name)])
        if user_search:
            return user_search
        else:
            raise Warning(_(' "%s" User not present.') % name)

    # def search_deliver(self, name):
    #     deliver_obj = self.env['stock.picking.type']
    #     deliver_search = deliver_obj.search([('name','=', name)])
    #     if deliver_search:
    #         return deliver_search
        # else:
        #     raise Warning(_(' "%s" Delivery not present.') % name)
        # pick_in = self.env.ref('stock.picking_type_in', raise_if_not_found=False)
        # company = self.env.company
        # if not pick_in or not pick_in.sudo().active or pick_in.sudo().warehouse_id.company_id.id != company.id:
        #     pick_in = deliver_obj.search(
        #         [('warehouse_id.company_id', '=', company.id), ('code', '=', 'incoming')],
        #         limit=1,
        #     )
        # return pick_in

    def search_partner(self, name):
        partner_obj = self.env['res.partner']
        partner_search = partner_obj.search([('name', '=', name)])
        # if not email:
        #     raise UserError(_('Please add email for %s' % name))
        if len(partner_search) > 1:
            partner_search = partner_obj.search([('name', '=', name)], limit=1)
        if partner_search:
            return partner_search
        else:
            partner_id = partner_obj.create({
                'name': name})
            return partner_id
    
    def search_payment_terms(self, name):
        payment_obj = self.env['account.payment.term']
        payment_search = payment_obj.search([('name', '=', name)])
        if len(payment_search) > 1:
            payment_search = payment_obj.search([('name', '=', name)], limit=1)
        if payment_search:
            return payment_search
        else:
            payment_id = payment_obj.create({
                'name': name})
            return payment_id
    
    def search_location(self, name):
        location_obj = self.env['stock.location']
        location_search = location_obj.search([('complete_name', '=', name)])
        if len(location_search) > 1:
            location_search = location_obj.search([('name', '=', name)], limit=1)
        if location_search:
            return location_search
        else:
            raise Warning(_(' "%s" Location Teams not present.') % name)
    
    def search_currency(self, name):
        currency_obj = self.env['res.currency']
        currency_search = currency_obj.search([('name', '=', name)])
        if currency_search:
            return currency_search
        else:
            raise Warning(_(' "%s" Currency not present.') % name)
    
    def make_deliv_date(self, date):
        DATETIME_FORMAT = "%Y-%m-%d"
        i_date = datetime.strptime(str(date), DATETIME_FORMAT)
        return i_date
    

    def import_purchase_order(self):

        """Load Inventory data from the CSV file."""
        if self.purchase_import_option == 'csv':
            keys = ['ref', 'vendor', 'deliver', 'product', 'quantity', 'uom', 'description', 'price', 'user',
                    'tax', 'date', 'payment', 'location', 'code', 'discount', 'plan_date', 'currency']
            try:
                csv_data = base64.b64decode(self.file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                file_reader = []
                csv_reader = csv.reader(data_file, delimiter=',')
            except Exception:
                raise exceptions.Warning(_("Please upload csv file !"))
            try:
                file_reader.extend(csv_reader)
            except Exception:
                raise exceptions.Warning(_("Invalid file!"))
            values = {}
            for i in range(len(file_reader)):
                field = list(map(str, file_reader[i]))
                values = dict(zip(keys, field))
                if values:
                    if i == 0:
                        continue
                    else:
                        values.update({'option': self.purchase_import_option, 'seq_opt': self.purchase_sequence_opt})
                        res = self.make_purchase_order(values)
                        if self.purchase_stage == 'confirm':
                            if res.state in ['draft', 'sent']:
                                res.button_confirm()
        else:
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            try:
                fp.write(binascii.a2b_base64(self.file))
                fp.seek(0)
                values = {}
                purchase_ids = []
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except Exception:
                raise exceptions.Warning(_("Please upload xlsx file !"))
            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    fields = map(lambda row: row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    get_line = list(
                        map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),
                            sheet.row(row_no)))
                    # if not get_line[11]:
                    #     raise UserError(_('Please add email for %s' % get_line[1]))
                    # a1 = get_line[10]
                    # date_string = datetime.strptime(a1, '%Y-%m-%d').date()
                    a1 = int(float(get_line[4]))
                    a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                    date_string = a1_as_datetime.date().strftime('%Y-%m-%d')

                    a2 = int(float(get_line[4]))
                    a2_as_datetime = datetime(*xlrd.xldate_as_tuple(a2, workbook.datemode))
                    date_string_a2 = a2_as_datetime.date().strftime('%Y-%m-%d')
 
                    values.update({'ref': get_line[0],
                                   'vendor': get_line[1],
                                   'currency': get_line[2],
                                #    'deliver': get_line[5],
                                   'location': get_line[6],
                                   'product': get_line[7],
                                   'uom': get_line[9],
                                   'tax': get_line[10],
                                #    'total': get_line[11],
                                   'analytic': get_line[12],
                                   'code': get_line[13],
                                   'price': get_line[15],
                                   'quantity': get_line[17],
                                #    'discount': get_line[13],
                                   'user': get_line[18],
                                #    'approve_date': date_string_a2,
                                   'date': date_string,
                                #    'email': get_line[11],
                                   'seq_opt': self.purchase_sequence_opt
                                   })

                    res = self.make_purchase_order(values)
                    purchase_ids.append(res)
                    if self.purchase_stage == 'confirm':
                        for res in purchase_ids:
                            if res.state in ['draft']:
                                res.button_confirm()
                    return res

