odoo.define('dashboard_custom.dashboard_snippet', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    
    publicWidget.registry.dashboardWidget = publicWidget.Widget.extend({
        selector: '.dashboard-component',
        events: {
            'click .dashboard-refresh-btn': '_onRefreshClick',
        },
        
        willStart: function() {
            console.log('Dashboard widget willStart');
            return this._super.apply(this, arguments);
        },
        
        start: function () {
            var self = this;
            console.log('Dashboard widget start called');
            
            // Make this work in both edit and view modes
            this.$refreshBtn = this.$('.dashboard-refresh-btn');
            
            // Add manual event handler as a backup
            this.$refreshBtn.on('click', function(ev) {
                console.log('Manual click event fired');
                ev.preventDefault();
                self._fullRefreshContent();
            });
            
            // Setup auto refresh
            this._setupAutoRefresh();
            
            console.log('Dashboard widget initialized!');
            return this._super.apply(this, arguments);
        },
        
        _onRefreshClick: function(ev) {
            console.log("Refresh button clicked through event binding!");
            ev.preventDefault();
            this._fullRefreshContent();
        },
        
        _setupAutoRefresh: function() {
            console.log('Setting up auto refresh');
            var self = this;
            // Set up timer for auto-refresh
            setInterval(function() {
                console.log('Auto refresh triggered');
                self._refreshData();
            }, 60000); // 1 minute
        },
        
        _refreshData: function() {
            console.log('Refreshing data...');
            var self = this;
            ajax.jsonRpc('/dashboard/refresh_data', 'call', {})
                .then(function (result) {
                    console.log('Data refresh result:', result);
                    if (result.error) {
                        console.error("Error refreshing dashboard:", result.error);
                        return;
                    }
                    
                    // Update all component values
                    _.each(result, function(data, id) {
                        var card = self.$el.find('[data-component-id="' + id + '"]');
                        if (card.length) {
                            card.find('.dashboard-card-value').text(data.value);
                        }
                    });
                })
                .catch(function(error) {
                    console.error("Failed to refresh dashboard data:", error);
                });
        },
        
        _fullRefreshContent: function() {
            console.log('Performing full refresh...');
            var self = this;
            // Show loading indicator
            self.$('.dashboard-content').addClass('o_loading');
            
            // Get fresh content
            ajax.jsonRpc('/dashboard/get_components', 'call', {})
                .then(function (result) {
                    console.log('Full refresh result:', result);
                    if (result.error) {
                        console.error("Error refreshing dashboard:", result.error);
                        self.$('.dashboard-content').removeClass('o_loading');
                        return;
                    }
                    
                    // Replace the entire content
                    self.$('.dashboard-content').html(result.html);
                    self.$('.dashboard-content').removeClass('o_loading');
                })
                .catch(function(error) {
                    console.error("Failed to refresh dashboard:", error);
                    self.$('.dashboard-content').removeClass('o_loading');
                });
        },
        
        destroy: function() {
            // Clean up any event handlers
            if (this.$refreshBtn) {
                this.$refreshBtn.off('click');
            }
            this._super.apply(this, arguments);
        }
    });
    
    // Force initialization on page load
    $(document).ready(function() {
        console.log("Document ready, checking for dashboard components");
        if ($('.dashboard-component').length > 0) {
            console.log("Found dashboard components on page");
        }
    });
    
    return publicWidget.registry.dashboardWidget;
});