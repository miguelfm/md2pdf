# Vega-Lite examples

## Histogram

```{.vega-lite width=85% caption="Histogram"}
{
  "data": {
    "values": [
      {
        "time": 12
      },
      {
        "time": 15
      },
      {
        "time": 15
      },
      {
        "time": 18
      },
      {
        "time": 22
      },
      {
        "time": 24
      },
      {
        "time": 25
      },
      {
        "time": 25
      },
      {
        "time": 26
      },
      {
        "time": 30
      }
    ]
  },
  "mark": "bar",
  "encoding": {
    "x": {
      "field": "time",
      "type": "quantitative",
      "bin": {
        "maxbins": 5
      },
      "title": "Time (ms)"
    },
    "y": {
      "aggregate": "count",
      "title": "Frequency"
    }
  }
}
```

## Scatter plot and linear regression

```{.vega-lite width=85% caption="Scatter plot and linear regression"}
{
  "data": {
    "values": [
      {
        "x": 1,
        "y": 2.1
      },
      {
        "x": 2,
        "y": 3.8
      },
      {
        "x": 3,
        "y": 6.2
      },
      {
        "x": 4,
        "y": 7.9
      },
      {
        "x": 5,
        "y": 10.3
      }
    ]
  },
  "encoding": {
    "x": {
      "field": "x",
      "type": "quantitative",
      "title": "Input"
    },
    "y": {
      "field": "y",
      "type": "quantitative",
      "title": "Measurement"
    }
  },
  "layer": [
    {
      "mark": {
        "type": "point",
        "filled": true
      }
    },
    {
      "transform": [
        {
          "regression": "y",
          "on": "x"
        }
      ],
      "mark": {
        "type": "line",
        "color": "#c43b35"
      }
    }
  ]
}
```

## Pie chart

```{.vega-lite width=85% caption="Pie chart"}
{
  "data": {
    "values": [
      {
        "type": "Reads",
        "value": 60
      },
      {
        "type": "Writes",
        "value": 25
      },
      {
        "type": "Other",
        "value": 15
      }
    ]
  },
  "mark": "arc",
  "encoding": {
    "theta": {
      "field": "value",
      "type": "quantitative"
    },
    "color": {
      "field": "type",
      "type": "nominal"
    }
  }
}
```


