from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class DashboardController(http.Controller):
    
    @http.route('/dashboard/refresh_data', type='json', auth='user', website=True)
    def refresh_dashboard_data(self):
        _logger.info("Dashboard refresh requested")
        try:
            # Get all active dashboard components
            components = request.env['dashboard.custom.component'].search([
                ('is_active', '=', True),
                ('component_type', '=', 'card')
            ])
            
            # Build result dictionary with component ID and calculated value
            result = {}
            for component in components:
                result[component.id] = {
                    'value': component._compute_card_data(),
                    'name': component.name,
                    'subtitle': component.card_subtitle or '',
                    'color': component.card_color,
                    'icon': component.icon or ''
                }
                
            _logger.info(f"Dashboard refresh successful, returning data for {len(components)} components")
            return result
        except Exception as e:
            _logger.error(f"Error refreshing dashboard data: {str(e)}")
            return {'error': str(e)}
    
    @http.route('/dashboard/get_components', type='json', auth='user', website=True)
    def get_dashboard_components(self):
        """Return the full HTML for all dashboard components"""
        try:
            # Get components
            components = request.env['dashboard.custom.component'].search([
                ('is_active', '=', True), 
                ('component_type', '=', 'card')
            ], order='sequence')
            
            # In Odoo 16, we use _render instead of render_template
            html = request.env['ir.qweb']._render(
                'dashboard_custom.dashboard_snippet_content',
                {'components': components}
            )
            
            return {'html': html}
        except Exception as e:
            _logger.error(f"Error getting dashboard components: {str(e)}")
            return {'error': str(e)}