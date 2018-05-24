# -*- coding: utf-8 -*-
{
    'name': "Cogito Synchronizer for JSON",

    'summary': """
        Cogito Synchronizer for JSON module""",

    'description': """
        Cogito Synchronizer for JSON

    """,

    'author': "Cogito",
    'website': "http://www.cogitoweb.it",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Manufactoring',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [ "synchronizer-main"],

    # always loaded
    'data': [ 

        #views
        'view/synchronizer_json.xml',
        #'view/synchronizer_record.xml',

        #menus
        #'view/synchronizer_xml_menu.xml',

    ],
    
    'qweb' : [
    ],

    # only loaded in demonstration mode
    'demo': [
    ],

    'application': True,
    'installable': True
}
