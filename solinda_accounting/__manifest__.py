# -*- coding: utf-8 -*-
{
    'name': "solinda_accounting",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'stock', 'sale','purchase','gls_reporting', 'sales_team'],

    # always loaded
    'data': [
        'report/action_report.xml',
        'views/views.xml',
        'views/sequence_data.xml',
        'views/account_move_views.xml',
        'views/account_asset_views.xml',
        'views/psak73_views.xml',
        'views/account_bank_statement.xml',
        'report/report_invoice_trading.xml',
        'report/report_invoice_boo.xml',
        'report/report_invoice_oms.xml',
        'report/report_invoice_turnkey.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True
}
