---
name: visualization-renderer
description: >
  Visualization Renderer — converts structured data into interactive ECharts charts and dashboards.
  4-Phase forced orchestration: data feature analysis -> ECharts config generation -> HTML page rendering -> dashboard multi-chart layout.
  Depends on diagram-drawing and web-artifacts-builder components, orchestrated via Phase-Orchestrator.
  Triggers: chart display, visualization, bar chart, line chart, pie chart, dashboard, kanban, data display.
name_cn: 可视化渲染
description_cn: 将结构化数据转换为交互式ECharts图表和Dashboard，支持自动图表推荐、多图编排
version: "1.0.0"
author: "yuzhaopeng"
license: "Apache-2.0"
---

# Visualization Renderer

Core visualization component. Converts structured data into interactive charts. Triggered when output_format is chart/dashboard.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| data | JSON | Yes | - | Aggregated data |
| chart_type | Option | No | auto | auto/bar/line/pie/table/scatter/radar/dashboard |
| title | Text | No | Data Query Result | Chart title |
| theme | Option | No | warm | warm/cool/dark/light |
| interactive | Switch | No | on | Tooltip, zoom, filter |

## Chart Recommendation Rules

| Data Feature | Recommended Chart | Reason |
|--------------|-------------------|--------|
| Single dimension + single metric + ranking | Horizontal bar | Intuitive comparison |
| Single dimension + single metric + proportion | Pie | Show proportional relationship |
| Time series + trend | Line | Show change trend |
| Multi dimension + multi metric | Grouped bar | Compare multiple dimensions |
| Multi metric correlation | Scatter | Show correlation |
| Comprehensive display | Dashboard | Multi-angle display |

## Supported Chart Types

| Type | ECharts type | Use Case | Data Requirement |
|------|-------------|----------|------------------|
| bar | bar | Ranking, comparison | 1 dimension + 1-3 metrics |
| line | line | Trend, time series | Time dimension + 1-3 metrics |
| pie | pie | Proportion, composition | 1 dimension + 1 metric |
| scatter | scatter | Correlation, distribution | 2 numeric metrics |
| radar | radar | Multi-dimensional evaluation | 3-8 metrics |
| table | table | Detailed data | Any structure |
| dashboard | mix | Comprehensive dashboard | Multiple data groups |

## 4-Phase Forced Orchestration Protocol

Orchestrated via Phase-Orchestrator. Each Phase launches a general-type sub-Agent via task tool.

### Phase 1: Data Feature Analysis and Chart Recommendation

Analyze data features and recommend chart type.

**Execution prompt** (injected into sub-Agent):

You are the Phase 1 executor of the Visualization Renderer. Analyze data features and recommend chart type.

**Step 1: Data feature extraction**

- Dimension count: 1/2/multiple/none
- Dimension type: categorical/temporal/numeric
- Metric count: 1/2/multiple
- Metric type: count/amount/ratio/duration
- Row count: small (<10)/medium (10-50)/large (>50)
- Special features: has_ranking/has_trend/has_proportion/has_comparison

**Step 2: Chart recommendation** (when chart_type=auto)

Auto-select based on recommendation rules table. When multiple charts fit, generate recommendation list with first as optimal choice, annotated with reason.

**Step 3: Color scheme**

- warm: #FF6B35, #F7C59F, #EFEFD0, #004E89, #1A659E
- cool: #2196F3, #00BCD4, #4CAF50, #FF9800, #9C27B0
- dark: dark background + bright colors
- light: light background + saturated colors

**Step 4: Interaction suggestions**

- Data > 10 rows -> enable dataZoom
- Multi dimension -> enable legend filter
- Has outliers -> add markPoint

**Output JSON**:
```json
{
  "chart_recommendation": {
    "primary": "bar",
    "alternatives": ["pie", "table"],
    "reason": "Single dimension ranking comparison, bar chart is most intuitive"
  },
  "data_features": {
    "dimension_count": 1,
    "dimension_type": "category",
    "metric_count": 1,
    "metric_type": "count",
    "row_count": 5,
    "has_ranking": true,
    "has_trend": false,
    "has_proportion": true
  },
  "color_scheme": ["#FF6B35", "#F7C59F", "#004E89", "#1A659E", "#EFEFD0"],
  "interaction_config": {
    "tooltip": true,
    "legend": true,
    "dataZoom": false,
    "markPoint": true
  },
  "phase_status": "success"
}
```

### Phase 2: ECharts Configuration Generation

Generate ECharts configuration JSON based on Phase 1 results.

**Execution prompt** (injected into sub-Agent):

You are the Phase 2 executor of the Visualization Renderer. Generate ECharts config based on Phase 1 analysis results.

**Base configuration structure**:
```json
{
  "title": {"text": "<title>", "left": "center"},
  "tooltip": {"trigger": "axis|item"},
  "legend": {"data": ["<metric_name>"], "bottom": 10},
  "xAxis": {"type": "category", "data": ["<dimension_value_list>"]},
  "yAxis": {"type": "value", "name": "<metric_unit>"},
  "series": [{"name": "<metric_name>", "type": "bar|line|pie", "data": [numeric_list]}]
}
```

**Chart-specific configuration**:

- **bar**: horizontal bar swaps xAxis/yAxis; grouped bar uses multiple series; stacked bar adds stack attribute; add label={show:true, position:"top"}
- **line**: smooth:true for curve; areaStyle:{opacity:0.3} for area chart; markPoint/markLine for data markers; time axis xAxis type:"time"
- **pie**: radius:["40%","70%"] for donut chart; labelLine for label guide lines; roseType:"area" for Nightingale chart
- **Theme colors**: color:["<Phase 1 color scheme>"]
- **Interaction**: dataZoom:[{type:"slider"}]; toolbox:{feature:{saveAsImage:{}, dataView:{readOnly:true}}}

**Output JSON**:
```json
{
  "echarts_option": { "...full ECharts configuration" },
  "chart_meta": {
    "chart_type": "bar",
    "dimensions": ["plan_type"],
    "metrics": ["ticket_count"],
    "data_points": 5
  },
  "phase_status": "success"
}
```

### Phase 3: HTML Page Generation

**Load component**: skill -> `web-artifacts-builder`

Generate a complete HTML page containing the ECharts chart.

**Execution prompt** (injected into sub-Agent):

You are the Phase 3 executor of the Visualization Renderer. Load web-artifacts-builder skill and generate an HTML page containing the ECharts chart.

**Page requirements**:

- **Structure**: header(title + query summary) -> main(ECharts chart container) -> footer(data source + generation time)
- **Tech stack**: ECharts CDN `https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js`, responsive layout, vanilla CSS
- **Style**: use Phase 1 warm theme colors, chart container width:100%/height:400px, card-style rounded 8px shadow, title 18px bold body 14px
- **Interaction**: legend toggle data series, hover tooltip, toolbox save image, window resize auto-fit
- Phase 2 echarts_option embedded in JavaScript initialization code

**Output JSON**:
```json
{
  "html_content": "<complete HTML string>",
  "page_meta": {
    "title": "<chart title>",
    "chart_count": 1,
    "responsive": true
  },
  "phase_status": "success"
}
```

### Phase 4: Dashboard Multi-Chart Layout (dashboard mode only)

**Condition**: Only executed when chart_type == "dashboard".

**Execution prompt** (injected into sub-Agent):

You are the Phase 4 executor of the Visualization Renderer. Layout dashboard multi-chart arrangement.

**Layout rules**:

- Grid: 2 columns (3 columns on large screen) auto-fit
- Top-left: primary metric bar/pie chart
- Top-right: trend line chart
- Bottom-left: TOP10 horizontal bar ranking
- Bottom-right: data detail table
- Unified title bar (title + time range selector), unified theme colors, global filter (region/time/plan type)
- Each chart has independent container and echarts_option, linkage: click one chart dimension -> other charts filter accordingly

**Output JSON**:
```json
{
  "dashboard_html": "<complete Dashboard HTML string>",
  "dashboard_meta": {
    "chart_count": 4,
    "layout": "2x2",
    "charts": [
      {"type": "bar", "title": "...", "position": "top-left"},
      {"type": "line", "title": "...", "position": "top-right"},
      {"type": "pie", "title": "...", "position": "bottom-left"},
      {"type": "table", "title": "...", "position": "bottom-right"}
    ]
  },
  "phase_status": "success"
}
```

## Phase Data Passing

- Phase 1 -> 2: `{ "chart_recommendation": {...}, "color_scheme": [...], "interaction_config": {...} }`
- Phase 2 -> 3: `{ "echarts_option": {...}, "chart_meta": {...} }`
- Phase 3 -> 4: `{ "html_content": "...", "page_meta": {...} }`

## Degradation Strategy

| Phase | Failure Handling |
|-------|-----------------|
| Phase 1 | Recommendation fails -> default to bar chart |
| Phase 2 | Config generation fails -> degrade to Markdown table |
| Phase 3 | HTML generation fails -> degrade to plain text data display |
| Phase 4 | Dashboard fails -> degrade to single chart |

## Usage Example

**Input**:
```json
{
  "data": [
    {"plan_type": "Premium Plan", "ticket_count": 47, "percentage": 33.6},
    {"plan_type": "Standard Plan", "ticket_count": 38, "percentage": 27.1},
    {"plan_type": "Basic Plan", "ticket_count": 25, "percentage": 17.9},
    {"plan_type": "Lite Plan", "ticket_count": 18, "percentage": 12.9},
    {"plan_type": "Enterprise Plan", "ticket_count": 12, "percentage": 8.6}
  ],
  "chart_type": "auto",
  "title": "Support Tickets by Plan - May 2026",
  "theme": "warm"
}
```

**Execution flow**: Phase 1 recommends -> bar (horizontal bar) -> Phase 2 generates ECharts config -> Phase 3 generates interactive HTML page
