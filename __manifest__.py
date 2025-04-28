{
    'name': 'Custom Dashboard Builder',
    'summary': 'Drag and drop dashboard builder using Odoo Website Builder',
    'description': 'Extend Odoo Website Builder to allow users to drag and drop custom dashboard components.',
    'author': 'Your Name',
    'website': 'https://yourwebsite.com',
    'category': 'Website',
    'version': '16.0.1.0.0',
    'license': 'LGPL-3',
    # 'depends': ['website', 'web'],
    'depends': ['website', 'web', 'in_clue_event_surveys'],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard_templates.xml',
        # 'views/dashboard_snippets.xml',
        'views/dashboard_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'dashboard_custom/static/src/js/dashboard_snippet.js',
        ],
    },
    'installable': True,
    'application': False,
}