# Admin Dashboard Design

**Date**: 2026-03-21
**Author**: Claude (via brainstorming session)
**Status**: Draft

## Overview

Design a comprehensive operational dashboard for admin users that replaces the current home page redirect, providing at-a-glance visibility into delivery performance, fleet efficiency, and data quality through interactive visualizations powered by Apache ECharts.

## Objectives

- Provide admin users with real-time operational insights through KPIs and trends
- Replace the current home page (`/`) redirect to `view_schedule` with a value-add dashboard
- Focus on high-impact operational metrics: delivery performance, fleet efficiency, and data quality
- Support both daily detail (7-day trends) and weekly aggregate views (30+ day periods)
- Enable quick access to common tasks through an action bar

## Key Requirements

### Access Control
- **Admin-only access**: Only users with `position == 'admin'` can view the dashboard
- Non-admin users continue to be redirected to `/view_schedule`
- Authenticated but unauthorized users see info message and redirect

### Data Scope
- **Primary focus**: Truck Utilization, Fuel Efficiency/ODO, and DIFOT metrics
- **Time granularity**: Mixed approach
  - Daily view for recent 7-day periods
  - Weekly aggregate view for 30+ day periods
- **Date range limits**: Maximum 90-day range to maintain performance
- **Auto-adjustment**: Future dates automatically clamp to today

### Performance Targets
- **Page load time**: < 3 seconds with 30 days of data
- **Refresh time**: < 2 seconds for manual refresh
- **Concurrent handling**: Disable refresh button during loading to prevent race conditions
- **Large dataset handling**: Auto-aggregate to weekly granularity if > 5000 records

## Architecture

### Backend API Layer

New Flask routes in `app.py`:

```
GET /api/dashboard/kpis
- Returns all 6 KPI summary values and trends
- Query params: start_date, end_date (default: last 7 days)
- Response: {
    on_time_delivery_rate: { value: 87.5, trend: +2.3 },
    in_full_delivery_rate: { value: 92.1, trend: -0.5 },
    difot_score: { value: 89.8, trend: +0.9 },
    truck_utilization: { value: 76.4, trend: +3.2 },
    fuel_efficiency: { value: 12.8, trend: -0.4 },
    fuel_cost_per_km: { value: 8.45, trend: +0.12 },
    data_completeness: { value: 94.2, trend: +1.1 }
  }

GET /api/dashboard/trends
- Time-series data for line charts
- Query params: start_date, end_date, granularity (daily/weekly)
- Response: {
    daily_deliveries: [{ date: '2026-03-14', count: 45 }, ...],
    fuel_efficiency: [{ date: '2026-03-14', km_per_liter: 12.5, cost_per_km: 8.20 }, ...],
    truck_utilization: [{ date: '2026-03-14', utilization_percent: 78.2 }, ...]
  }

GET /api/dashboard/comparisons
- Ranked data for bar charts
- Query params: start_date, end_date
- Response: {
    vehicle_utilization: [{ plate_number: 'ABC-123', utilization: 85.2, rank: 1 }, ...],
    branch_frequency: [{ branch: 'Manila', delivery_count: 156, rank: 1 }, ...],
    driver_performance: [{ name: 'Juan Dela Cruz', trips: 42, role: 'driver', rank: 1 }, ...]
  }

GET /api/dashboard/gauges
- Current values for gauge displays
- Response: {
    on_time_rate: 87.5,
    utilization: 76.4,
    data_completeness: 94.2
  }
```

### Data Computation Logic

**On-Time Delivery Rate**:
```python
on_time_count = db.session.query(Trip).join(Schedule).filter(
    Trip.scheduled_date <= Trip.original_due_date,
    Trip.scheduled_date.between(start_date, end_date)
).count()

total_deliveries = db.session.query(Trip).filter(
    Trip.scheduled_date.between(start_date, end_date)
).count()

on_time_rate = (on_time_count / total_deliveries * 100) if total_deliveries > 0 else 0
```

**In-Full Delivery Rate**:
```python
in_full_count = db.session.query(Trip).filter(
    Trip.total_delivered_qty >= Trip.total_ordered_qty,
    Trip.scheduled_date.between(start_date, end_date)
).count()

in_full_rate = (in_full_count / total_deliveries * 100) if total_deliveries > 0 else 0
```

**DIFOT Score**:
```python
difot_score = (on_time_rate + in_full_rate) / 2
```

**Truck Utilization**:
```python
utilization_records = db.session.query(
    Vehicle.capacity,
    func.sum(TripDetail.actual_cbm).label('total_actual')
).join(Trip).join(Schedule).filter(
    Schedule.delivery_schedule.between(start_date, end_date)
).group_by(Vehicle.plate_number, Vehicle.capacity).all()

utilization_percent = sum([
    (r.total_actual / r.capacity * 100) for r in utilization_records if r.capacity > 0
]) / len(utilization_records) if utilization_records else 0
```

**Fuel Efficiency**:
```python
# KM per liter per vehicle
odo_records = db.session.query(Odo).filter(
    Odo.datetime.between(start_datetime, end_datetime)
).order_by(Odo.datetime).all()

# Calculate distance traveled and fuel consumed per vehicle
# Weighted average by distance
```

**Data Completeness**:
```python
total_trips = db.session.query(Trip).join(Schedule).filter(
    Schedule.delivery_schedule.between(start_date, end_date)
).count()

trips_missing_arrival = db.session.query(Trip).join(Schedule).filter(
    Schedule.delivery_schedule.between(start_date, end_date),
    Trip.arrive_time.is_(None)
).count()

trips_missing_odo = db.session.query(Schedule).filter(
    Schedule.delivery_schedule.between(start_date, end_date),
    ~Schedule.odo_records.any()
).count()

completeness = ((total_trips - trips_missing_arrival - trips_missing_odo) / total_trips * 100) if total_trips > 0 else 0
```

### Frontend Architecture

**Template Structure** (`templates/dashboard.html`):
```
dashboard.html (extends base.html)
├── Action Bar (fixed top)
│   ├── Logo/title
│   ├── Quick action buttons
│   └── User info + Refresh + Timestamp
├── KPI Summary Cards (6 cards, 2×3 grid)
├── Main Chart Section (2-column layout)
│   ├── Left Column: Trend Line Charts
│   │   ├── Daily delivery counts
│   │   ├── Fuel efficiency (dual-axis)
│   │   └── Truck utilization
│   └── Right Column: Comparison Bar Charts
│       ├── Vehicle utilization ranking
│       ├── Branch delivery frequency
│       └── Driver/assistant performance
└── Performance Gauges (3 gauges in row)
```

**JavaScript Modules**:
- `dashboard-api.js`: API client functions (fetchKPIs, fetchTrends, fetchComparisons, fetchGauges)
- `dashboard-charts.js`: ECharts initialization and update functions
- `dashboard-main.js`: Main controller, event handlers, refresh logic
- `dashboard-utils.js`: Helper functions (date formatting, trend calculation, color coding)

**Data Loading Strategy**:
```javascript
// Parallel fetch on initial load
Promise.all([
  fetch('/api/dashboard/kpis').then(r => r.json()),
  fetch('/api/dashboard/trends').then(r => r.json()),
  fetch('/api/dashboard/comparisons').then(r => r.json()),
  fetch('/api/dashboard/gauges').then(r => r.json())
])
.then(([kpis, trends, comparisons, gauges]) => {
  renderKPIs(kpis);
  renderTrendCharts(trends);
  renderComparisonCharts(comparisons);
  renderGauges(gauges);
  updateTimestamp();
})
.catch(handleDashboardError);

// Manual refresh
document.getElementById('refreshBtn').addEventListener('click', () => {
  refreshDashboard(); // Re-runs Promise.all
});
```

## Layout & Visual Design

### Color Scheme

**Performance Tiers**:
- Green (Good): On-Time ≥90%, Utilization ≥80%, Completeness ≥95%
- Yellow (Caution): On-Time 70-89%, Utilization 50-79%, Completeness 85-94%
- Red (Needs Attention): On-Time <70%, Utilization <50%, Completeness <85%

**Chart Palette**: Professional 5-color scheme
- Primary: #3b82f6 (blue)
- Secondary: #14b8a6 (teal)
- Tertiary: #8b5cf6 (purple)
- Quaternary: #f97316 (orange)
- Neutral: #6b7280 (gray)

**KPI Card Design**:
- Compact 200px height, white background, subtle shadow
- Layout: Icon (left) → Value (center) → Sparkline (right)
- Bottom: "View details →" link scrolls to relevant chart
- Icon colored by performance tier (green/yellow/red)

### Chart Specifications

**Line Charts (Trends)**:
- Delivery Counts: Smooth curved line, gradient area fill, tooltips on hover
- Fuel Efficiency: Dual-axis chart (blue line for KM/Liter, orange for cost/KM)
- Truck Utilization: Step-line chart, horizontal target line at 80%
- All: Data zoom slider at bottom, legend toggle for series

**Bar Charts (Comparisons)**:
- Vehicle Utilization: Horizontal bars, sorted by %, color-coded by performance tier
- Branch Frequency: Vertical bars, top 10 + "Others" aggregate, count labels on bars
- Driver Performance: Vertical bars, trip count, different color for drivers vs assistants

**Gauge Charts**:
- Semi-circular (180°), 3 gauges in a row
- Color bands: Red (0-50%), Yellow (50-80%), Green (80-100%)
- Needle pointer + percentage text in center
- Subtitle: "Target: 80%" (placeholder reference)

### Responsive Design

**Desktop (≥992px)**:
- 2-column chart layout
- 3×2 KPI grid (3 columns, 2 rows)
- Full ECharts interactivity

**Tablet (768-991px)**:
- Stacked charts (single column)
- 2×3 KPI grid (2 columns, 3 rows)
- Reduced chart heights

**Mobile (<768px)**:
- Single column layout
- Stacked KPI cards (1 column)
- Simplified charts (hide secondary y-axes, smaller fonts)
- Action bar collapses to hamburger menu

## Error Handling & Edge Cases

### No Data Scenarios
- **Empty date range**: Show "No data available for selected period" in each chart, display "—" in KPI cards
- **Missing ODO records**: Calculate with available data, show "⚠️ Partial data" badge
- **New vehicles** (< 7 days): Include in calculations, mark with "New" tooltip

### Data Validation
- **Invalid date ranges**: Client-side prevents end_date before start_date, max 90-day limit
- **Future dates**: Auto-adjust end_date to today
- **Extreme values**: Filter outliers (KM/Liter > 100 or < 2), show filtered data note

### Performance Edge Cases
- **Large datasets** (> 5000 records): Auto-aggregate to weekly granularity
- **Slow queries**: Show loading spinners, progressive rendering
- **Concurrent refreshes**: Disable refresh button during loading

### API Error Handling
- Format: `{"error": "Human-readable message", "details": "Technical context"}`
- Client displays dismissible error banner at top
- Failed chart sections show "Unable to load data. Retry?" button

### Browser Compatibility
- **Supported**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Graceful degradation**: Show table-based fallback if canvas rendering fails

## Implementation Phases

### Phase 1: Foundation
- Create Flask route `/` with admin permission check
- Build `templates/dashboard.html` with action bar and grid layout
- Add Bootstrap Icons library
- Set up responsive layout (mobile-first)

### Phase 2: Backend API Development
- Implement `GET /api/dashboard/kpis` with SQLAlchemy aggregations
- Implement `GET /api/dashboard/trends` with time-series data
- Implement `GET /api/dashboard/comparisons` with ranked data
- Implement `GET /api/dashboard/gauges` with current values
- Add query parameter handling
- Write unit tests for KPI calculations

### Phase 3: Frontend Integration
- Add Apache ECharts library via CDN
- Implement KPI card rendering with data binding
- Create line chart components (3 charts)
- Create bar chart components (3 charts)
- Create gauge chart components (3 charts)
- Implement refresh functionality

### Phase 4: Polish & Optimization
- Add loading spinners and progressive rendering
- Implement error handling and user-friendly messages
- Add responsive breakpoints
- Optimize slow queries with database indexes if needed
- Test cross-browser compatibility

### Phase 5: Documentation & Deployment
- Update CLAUDE.md with dashboard architecture
- Document API endpoints in code comments
- Create user guide markdown
- Deploy to staging for UAT
- Monitor and optimize based on usage

**Estimated Effort**: 1 week (5-7 days) for full implementation

## Testing Strategy

### Unit Testing (Backend)
- KPI calculations with known data sets
- Edge cases: empty datasets, single record, all-missing data
- Date range handling: future dates, inverted ranges, 90+ day ranges
- Permission checks: admin vs non-admin access

### Integration Testing (API)
- Verify all 4 endpoints return valid JSON structure
- Test with production-like data volumes (1000+ records)
- Verify query parameter filtering
- Test error response format

### Frontend Testing (Charts)
- Manual testing: Chart rendering with different data sizes
- Browser testing: Chrome, Firefox, Safari, Edge (latest versions)
- Responsive testing: Desktop (1920×1080), tablet (768×1024), mobile (375×667)
- Interaction testing: Tooltips, legend toggles, zoom sliders

### User Acceptance Testing (Admin Workflow)
- Can admin users load dashboard and see all KPIs?
- Does refresh button update data correctly?
- Do quick action links work?
- Is dashboard readable and actionable?
- Performance: < 3 seconds load time with 30 days data

### Regression Testing (Existing Features)
- Verify `/reports` page still works
- Confirm non-admin users still redirect to `/view_schedule`
- Test all quick action links navigate correctly
- Ensure no breaking changes to existing routes

### Success Criteria
- Dashboard loads in < 3 seconds with 30 days of data
- All 6 KPIs calculate correctly (verified against manual calculations)
- Charts render without errors across all supported browsers
- Admin users can access dashboard, non-admins cannot
- Refresh functionality works reliably
- Mobile view is functional for basic monitoring

## Dependencies & Libraries

### Backend (Flask)
- Flask 3.1.3 (existing)
- Flask-SQLAlchemy 3.1.1 (existing)
- Flask-Login 0.6.3 (existing)
- pytz (existing, for timezone handling)

### Frontend
- Apache ECharts 5.x (via CDN)
- Bootstrap Icons 1.x (via CDN, if not already present)
- Bootstrap CSS (existing)

### Optional Enhancements
- Flask-Caching (SimpleCache already in codebase)
- Database indexes on frequently queried fields

## Open Questions & Future Enhancements

### Phase 2 Enhancements (Not in initial scope)
- Custom target thresholds for KPIs (currently using placeholder 80%)
- Scheduled report delivery (email dashboard PDF on schedule)
- User-role customization (different views for admins, coordinators)
- Historical comparison (compare current period vs previous period)
- Public share link for read-only dashboard access

### Data Quality Improvements
- Automated data quality alerts (email when completeness < 85%)
- Trend anomaly detection (flag unusual spikes/drops)
- Predictive analytics (forecast utilization based on trends)

### Interactive Features
- Drill-down from KPI cards to detailed filtered reports
- Custom date range presets (Last 7 days, Last 30 days, This Month)
- Export dashboard as PDF/image
- Customizable dashboard layout (user can rearrange cards)

## Metrics & Success Measurement

- **Dashboard adoption**: % of admin users who access dashboard daily/weekly
- **Page load performance**: Average load time (target: < 3 seconds)
- **Data quality improvement**: Trend in data completeness % over time
- **User satisfaction**: Feedback from admin users after 2 weeks of use
- **Operational impact**: Correlation between dashboard visibility and KPI improvements

---

**Next Steps**: After approval, this spec will be used to create a detailed implementation plan using the writing-plans skill.
