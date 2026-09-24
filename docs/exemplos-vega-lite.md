# Exemplos de Vega-Lite

## Histograma

```{.vega-lite width=85% caption="Histograma"}
{
  "data": {
    "values": [
      {
        "tempo": 12
      },
      {
        "tempo": 15
      },
      {
        "tempo": 15
      },
      {
        "tempo": 18
      },
      {
        "tempo": 22
      },
      {
        "tempo": 24
      },
      {
        "tempo": 25
      },
      {
        "tempo": 25
      },
      {
        "tempo": 26
      },
      {
        "tempo": 30
      }
    ]
  },
  "mark": "bar",
  "encoding": {
    "x": {
      "field": "tempo",
      "type": "quantitative",
      "bin": {
        "maxbins": 5
      },
      "title": "Tempo (ms)"
    },
    "y": {
      "aggregate": "count",
      "title": "Frecuencia"
    }
  }
}
```

## Puntos e regresión lineal

```{.vega-lite width=85% caption="Puntos e regresión lineal"}
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
      "title": "Entrada"
    },
    "y": {
      "field": "y",
      "type": "quantitative",
      "title": "Medición"
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

## Gráfico de sectores

```{.vega-lite width=85% caption="Gráfico de sectores"}
{
  "data": {
    "values": [
      {
        "tipo": "Lecturas",
        "valor": 60
      },
      {
        "tipo": "Escrituras",
        "valor": 25
      },
      {
        "tipo": "Outras",
        "valor": 15
      }
    ]
  },
  "mark": "arc",
  "encoding": {
    "theta": {
      "field": "valor",
      "type": "quantitative"
    },
    "color": {
      "field": "tipo",
      "type": "nominal"
    }
  }
}
```


