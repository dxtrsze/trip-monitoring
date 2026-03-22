// Dashboard utility functions

// Format date as localized string
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// Format percentage with 1 decimal place
function formatPercent(value) {
  return value.toFixed(1) + '%';
}

// Format number with commas
function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Get performance tier color for KPIs
function getPerformanceColor(value, type) {
  const thresholds = {
    on_time: { good: 90, caution: 70 },
    utilization: { good: 80, caution: 50 },
    completeness: { good: 95, caution: 85 }
  };

  const tier = thresholds[type];
  if (!tier) return 'gray';

  if (value >= tier.good) return '#10b981'; // green
  if (value >= tier.caution) return '#f59e0b'; // yellow
  return '#ef4444'; // red
}

// Get Bootstrap icon class for KPI
function getKPIIcon(kpiName) {
  const icons = {
    on_time_delivery_rate: 'bi-clock-history',
    in_full_delivery_rate: 'bi-check-circle',
    difot_score: 'bi-graph-up-arrow',
    truck_utilization: 'bi-truck',
    fuel_efficiency: 'bi-fuel-pump',
    data_completeness: 'bi-file-check'
  };
  return icons[kpiName] || 'bi-bar-chart';
}

// Get trend arrow HTML
function getTrendHtml(trend) {
  if (trend > 0) {
    return `<span class="text-success"><i class="bi bi-arrow-up"></i> ${trend}</span>`;
  } else if (trend < 0) {
    return `<span class="text-danger"><i class="bi bi-arrow-down"></i> ${Math.abs(trend)}</span>`;
  } else {
    return '<span class="text-secondary"><i class="bi bi-dash"></i> 0</span>';
  }
}

// Calculate "time ago" string
function timeAgo(date) {
  const seconds = Math.floor((new Date() - date) / 1000);

  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return Math.floor(seconds / 60) + ' minutes ago';
  if (seconds < 86400) return Math.floor(seconds / 3600) + ' hours ago';
  return Math.floor(seconds / 86400) + ' days ago';
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    formatDate,
    formatPercent,
    formatNumber,
    getPerformanceColor,
    getKPIIcon,
    getTrendHtml,
    timeAgo
  };
}
