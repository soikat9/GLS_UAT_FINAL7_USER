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


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _description = 'Inherited Sale Order'

    custom_sequence = fields.Boolean('Custom Sequence')
    system_sequence = fields.Boolean('System Sequence')


class ImportSaleOrder(models.TransientModel):
    _name = "import.sale.order"
    _description = 'Import Sale Order'

    file = fields.Binary('Upload File')
    sales_sequence_opt = fields.Selection(
        [('custom', 'Use Excel/CSV Sequence Number'), ('system', 'Use System Default Sequence Number')],
        string='Sequence Available', default='custom')
    sale_import_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='File Type', default='csv')
    sales_stage = fields.Selection(
        [('draft', 'Import Quotation in Draft Stage'), ('confirm', 'Confirm Quotation Automatically while Importing')],
        string="Quotation State Available", default='draft')
    import_product_search = fields.Selection([('by_code', 'Search By Code'), ('by_name', 'Search By Name'), ('by_ids', 'Search By ID')],
                                             string='Product Search Option', default='by_code')

    def make_sale_order(self, values):
        sale_obj = self.env['sale.order']
        sale_search = sale_obj.search([
            ('name', '=', values.get('order'))
        ])
        payment_term = self.env['account.payment.term']
        if sale_search:
            # if sale_search.payment_term_id.name == values.get('payment'):
            if sale_search.partner_id.name == values.get('customer'):
                if sale_search.pricelist_id.name == values.get('pricelist'):
                    lines = self.make_sale_order_line(values, sale_search)
                    return sale_search
                else:
                    raise Warning(
                        _('Pricelist is different for "%s" .\n Please define same.') % values.get('order'))
            else:
                raise Warning(
                    _('Customer name is different for "%s" .\n Please define same.') % values.get('order'))
            # else:
            #     raise Warning(_('Payment Termss is different for "%s" .\n Please define same.') % values.get('order'))

        else:
            if values.get('seq_opt') == 'system':
                name = self.env['ir.sequence'].next_by_code('sale.order')
            elif values.get('seq_opt') == 'custom':
                name = values.get('order')
            partner_id = self.search_partner(values.get('customer'))
            currency_id = self.search_currency(values.get('pricelist'))
            user_id = self.search_user(values.get('user'))
            order_date = self.make_order_date(values.get('date'))
            payment_id = self.search_payment_terms(values.get('payment'))
            team_id = self.search_sales_teams(values.get('team'))
            ref = values.get('ref')
            tag_id = self.search_tag(values.get('tag'))
            warehouse_id = self.search_warehouse(values.get('warehouse'))
            deliv_date = self.make_deliv_date(values.get('deliv_date'))

            sale_id = sale_obj.create({
                'partner_id': partner_id.id,
                'pricelist_id': currency_id.id,
                'name': name,
                'user_id': user_id.id,
                'date_order': order_date,
                'payment_term_id': payment_id.id,
                'team_id': team_id.id,
                'client_order_ref': ref,
                'tag_ids': tag_id.ids,
                'warehouse_id': warehouse_id.id,
                'commitment_date': deliv_date,
                'custom_sequence': True if values.get('seq_opt') == 'custom' else False,
                'system_sequence': True if values.get('seq_opt') == 'system' else False,
            })
            lines = self.make_sale_order_line(values, sale_id)
            return sale_id

    def make_sale_order_line(self, values, sale_id):
        product_obj = self.env['product.product']
        order_line_obj = self.env['sale.order.line']
        product_uom = self.env['uom.uom'].search([('name', '=', values.get('uom'))])
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
                    tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'sale')])
                    if not tax:
                        raise Warning(_('"%s" Tax not present in your system') % name)
                    tax_ids.append(tax.id)

            elif ',' in values.get('tax'):
                tax_names = values.get('tax').split(',')
                for name in tax_names:
                    tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'sale')])
                    if not tax:
                        raise Warning(_('"%s" Tax not present in your system') % name)
                    tax_ids.append(tax.id)
            else:
                tax_names = values.get('tax')
                tax = self.env['account.tax'].search([('name', '=', tax_names), ('type_tax_use', '=', 'sale')])
                if not tax:
                    raise Warning(_('"%s" Tax not present in your system') % tax_names)
                tax_ids.append(tax.id)

        if not product_uom:
            raise Warning(_(' "%s" Product UOM category is not present.') % values.get('uom'))

        res = order_line_obj.create({
            'product_id': product_id.id,
            'product_uom_qty': values.get('quantity'),
            'price_unit': values.get('price'),
            'name': values.get('description'),
            'product_uom': product_uom.id,
            'order_id': sale_id.id,
            'qty_delivered': values.get('delivered_qty'),
            'qty_invoiced': values.get('invoiced_qty'),
            'discount': values.get('discount')

        })
        if tax_ids:
            res.write({'tax_id': ([(6, 0, tax_ids)])})
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

    def search_currency(self, name):
        currency_obj = self.env['product.pricelist']
        currency_search = currency_obj.search([('name', '=', name)])
        if currency_search:
            return currency_search
        else:
            raise Warning(_(' "%s" Pricelist are not available.') % name)

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
    
    def search_sales_teams(self, name):
        teams_obj = self.env['crm.team']
        teams_search = teams_obj.search([('name', '=', name)])
        if teams_search:
            return teams_search
        else:
            raise Warning(_(' "%s" Sales Teams not present.') % name)
    
    def search_tag(self, name):
        tag_obj = self.env['crm.tag']
        tag_search = tag_obj.search([('name', '=', name)])
        if tag_search:
            return tag_search
        else:
            raise Warning(_(' "%s" Tags not present.') % name)
    
    def search_warehouse(self, name):
        warehouse_obj = self.env['stock.warehouse']
        warehouse_search = warehouse_obj.search([('name', '=', name)])
        if warehouse_search:
            return warehouse_search
        else:
            raise Warning(_(' "%s" Warehouse not present.') % name)
    
    def make_deliv_date(self, date):
        DATETIME_FORMAT = "%Y-%m-%d"
        i_date = datetime.strptime(str(date), DATETIME_FORMAT)
        return i_date
    

    def import_sale_order(self):

        """Load Inventory data from the CSV file."""
        if self.sale_import_option == 'csv':
            keys = ['order', 'customer', 'pricelist', 'product', 'quantity', 'uom', 'description', 'price', 'user',
                    'tax', 'date', 'payment', 'delivered_qty', 'invoiced_qty', 'discount', 'team', 'ref',
                    'tag', 'warehouse', 'deliv_date']
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
                        values.update({'option': self.sale_import_option, 'seq_opt': self.sales_sequence_opt})
                        res = self.make_sale_order(values)
                        if self.sales_stage == 'confirm':
                            if res.state in ['draft', 'sent']:
                                res.action_confirm()
        else:
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            try:
                fp.write(binascii.a2b_base64(self.file))
                fp.seek(0)
                values = {}
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
                    a1 = int(float(get_line[2]))
                    a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                    date_string = a1_as_datetime.date().strftime('%Y-%m-%d')

                    a2 = int(float(get_line[20]))
                    a2_as_datetime = datetime(*xlrd.xldate_as_tuple(a2, workbook.datemode))
                    date_string_a2 = a2_as_datetime.date().strftime('%Y-%m-%d')

                    values.update({'order': get_line[0],
                                   'customer': get_line[1],
                                   'payment': get_line[3],
                                   'pricelist': get_line[4],
                                   'product': get_line[5],
                                   'description': get_line[6],
                                   'quantity': get_line[7],
                                   'delivered_qty': get_line[8],
                                   'invoiced_qty': get_line[9],
                                   'uom': get_line[10],
                                   'price': get_line[11],
                                   'tax': get_line[12],
                                   'discount': get_line[13],
                                   'total': get_line[14],
                                   'user': get_line[15],
                                   'team': get_line[16],
                                   'ref': get_line[17],
                                   'tag': get_line[18],
                                   'warehouse': get_line[19],
                                   'deliv_date': date_string_a2,
                                   'date': date_string,
                                #    'email': get_line[11],
                                   'seq_opt': self.sales_sequence_opt
                                   })

                    res = self.make_sale_order(values)
                    if self.sales_stage == 'confirm':
                        if res.state in ['draft', 'sent']:
                            res.action_confirm()

        return res
