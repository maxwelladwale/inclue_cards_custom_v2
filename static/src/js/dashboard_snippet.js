odoo.define('dashboard_custom.dashboard_snippet', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    var options = require('web_editor.snippets.options');
    
    // Define snippet options
    options.registry.dashboard_widget = options.Class.extend({
        start: function () {
            var self = this;
            return this._super.apply(this, arguments);
        },
    });
    
    // Define frontend widget
    publicWidget.registry.dashboardWidget = publicWidget.Widget.extend({
        selector: '.dashboard-component',
        
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                // Initialize your dashboard functionality here
                console.log('Dashboard widget initialized!');
                // Refresh data periodically if needed
                self._refreshData();
            });
        },
        
        _refreshData: function() {
            // Refresh data periodically using AJAX
            var self = this;
            setTimeout(function() {
                // Make an AJAX call to refresh data
                ajax.jsonRpc('/dashboard/refresh_data', 'call', {})
                   .then(function (result) {
                       // Update component values with new data
                       _.each(result, function(value, id) {
                           self.$el.find('.dashboard-card-value[data-component-id="' + id + '"]').text(value);
                       });
                   });
                
                self._refreshData(); // Schedule next refresh
            }, 60000); // 1 minute
        }
    });
});