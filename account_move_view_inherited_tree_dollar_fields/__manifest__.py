# -*- coding: utf-8 -*-
{
    'name': "Dollar fields",

    'summary': """Dollar fields""",
    'description': """This module inherits the tree 
    view of account.move in the customer invoice 
    and adds columns with dollar fields related 
    to the total, amount owed,tax and tax excluded""",
    'author': "IT Sales",
    'website': "http://www.itsalescorp.com",
    'category': 'Sales',
    'version': '0.1',
    'depends': ['base','account'],
    'data': [
        'views/account_move_view_inherited_tree_dollar_fields.xml',
    ],
}
