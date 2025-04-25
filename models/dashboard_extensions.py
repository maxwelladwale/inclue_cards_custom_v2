from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class DashboardComponent(models.Model):
    _inherit = "dashboard.custom.component"
    
    # Add new component types specific to iN-Clue
    component_type = fields.Selection(selection_add=[
        ('inclue_stats', 'iN-Clue Statistics')
    ])
    
    # Add new calculation types for iN-Clue
    calculation_type = fields.Selection(selection_add=[
        ('completion_rate', 'Survey Completion Rate'),
        ('facilitator_performance', 'Facilitator Performance')
    ])
    
    # Add a new field for facilitator filtering
    facilitator_id = fields.Many2one('res.partner', string='Filter by Facilitator',
                                    domain="[('is_facilitator', '=', True)]")
    
    # Add a new field for session type filtering
    session_type = fields.Selection([
        ('all', 'All Sessions'),
        ('kickoff', 'Kickoff Only'),
        ('followup', 'Follow-ups Only')
    ], string="Session Type Filter", default='all')
    
    # Override to add special calculations for iN-Clue
    def _compute_card_data(self):
        """Compute the data to be displayed on the card"""
        self.ensure_one()
        
        # If this isn't an iN-Clue calculation, use the standard computation
        if self.calculation_type not in ['completion_rate', 'facilitator_performance']:
            return super(DashboardComponent, self)._compute_card_data()
            
        try:
            # Special calculations for iN-Clue
            if self.calculation_type == 'completion_rate':
                return self._compute_completion_rate()
            elif self.calculation_type == 'facilitator_performance':
                return self._compute_facilitator_performance()
                
        except Exception as e:
            _logger.error(f"Error in iN-Clue dashboard calculation: {str(e)}")
            return f"Error: {str(e)[:20]}"
    
    def _compute_completion_rate(self):
        """Calculate survey completion rate"""
        domain = []
        
        # Apply base domain if specified
        if self.domain and self.domain != "[]":
            try:
                from odoo.tools.safe_eval import safe_eval
                base_domain = safe_eval(self.domain)
                domain.extend(base_domain)
            except Exception as e:
                return f"Domain Error: {str(e)[:20]}"
        
        # Apply facilitator filter if specified
        if self.facilitator_id:
            domain.append(('facilitator_id', '=', self.facilitator_id.id))
        
        # Apply session type filter if specified
        if self.session_type == 'kickoff':
            domain.append(('session_type', '=', 'kickoff'))
        elif self.session_type == 'followup':
            domain.append(('session_type', '!=', 'kickoff'))
        
        # Get the participation records
        participations = self.env['inclue.participation'].search(domain)
        
        if not participations:
            return "0%"
        
        # Calculate completion rate
        total = len(participations)
        completed = len(participations.filtered(lambda p: p.completed))
        
        completion_rate = (completed / total) * 100 if total > 0 else 0
        return f"{round(completion_rate)}%"
    
    def _compute_facilitator_performance(self):
        """Calculate facilitator performance metrics"""
        domain = []
        
        # Apply base domain if specified
        if self.domain and self.domain != "[]":
            try:
                from odoo.tools.safe_eval import safe_eval
                base_domain = safe_eval(self.domain)
                domain.extend(base_domain)
            except Exception as e:
                return f"Domain Error: {str(e)[:20]}"
        
        # Apply facilitator filter if specified
        if self.facilitator_id:
            domain.append(('facilitator_id', '=', self.facilitator_id.id))
        
        # Get the participation records
        participations = self.env['inclue.participation'].search(domain)
        
        if not participations:
            return "0"
        
        # Get unique events facilitated
        events = participations.mapped('event_id')
        
        # Get unique participants
        participants = participations.mapped('partner_id')
        
        # Calculate completion rate
        total = len(participations)
        completed = len(participations.filtered(lambda p: p.completed))
        completion_rate = (completed / total) * 100 if total > 0 else 0
        
        # Return the score based on what field is set to count
        if self.count_field == 'events':
            return str(len(events))
        elif self.count_field == 'participants': 
            return str(len(participants))
        elif self.count_field == 'completion_rate':
            return f"{round(completion_rate)}%"
        else:
            # Default to events count if no field specified
            return str(len(events))