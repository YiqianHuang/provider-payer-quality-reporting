# DAX Measure Inventory

The canonical machine-readable expressions are in
`powerbi/semantic_model.json`. Raw rates, ratios, ratings, and scores must not
be implicitly summed.

## Counts and availability

```DAX
Facility Count :=
DISTINCTCOUNT ( 'Dim Facility'[Facility ID] )
```

```DAX
Reportable Provider Results :=
CALCULATE (
    COUNTROWS ( 'Fact Provider Measure' ),
    'Fact Provider Measure'[Is Reportable] = TRUE ()
)
```

```DAX
Suppressed Provider Results :=
CALCULATE (
    COUNTROWS ( 'Fact Provider Measure' ),
    'Fact Provider Measure'[Is Suppressed] = TRUE ()
)
```

```DAX
Reportable Result Percent :=
DIVIDE (
    [Reportable Provider Results],
    COUNTROWS ( 'Fact Provider Measure' )
)
```

## Provider result and benchmark

```DAX
Selected Provider Score :=
IF (
    SELECTEDVALUE ( 'Fact Provider Measure'[Is Reportable] ) = TRUE (),
    SELECTEDVALUE ( 'Fact Provider Measure'[Score] ),
    BLANK ()
)
```

```DAX
Selected National Benchmark :=
SELECTEDVALUE ( 'Fact National Benchmark'[National Rate] )
```

```DAX
Direction Adjusted Gap :=
VAR ProviderValue = [Selected Provider Score]
VAR BenchmarkValue = [Selected National Benchmark]
VAR Direction = SELECTEDVALUE ( 'Dim Measure'[Direction] )
RETURN
    IF (
        ISBLANK ( ProviderValue ) || ISBLANK ( BenchmarkValue ),
        BLANK (),
        SWITCH (
            Direction,
            "Lower is better", BenchmarkValue - ProviderValue,
            "Higher is better", ProviderValue - BenchmarkValue,
            BLANK ()
        )
    )
```

A positive direction-adjusted gap means better performance relative to the
official national value. It is blank for EDAC and OP-36 because the national
file publishes `Not Applicable` rather than a numeric rate.

## CMS comparison categories

```DAX
Better Result Count :=
CALCULATE (
    COUNTROWS ( 'Fact Provider Measure' ),
    'Fact Provider Measure'[Comparison Category]
        IN {
            "Better than national rate",
            "Better than expected",
            "Fewer days than average"
        }
)
```

```DAX
Same Result Count :=
CALCULATE (
    COUNTROWS ( 'Fact Provider Measure' ),
    'Fact Provider Measure'[Comparison Category]
        IN {
            "No different than national rate",
            "No different than expected",
            "Average days"
        }
)
```

```DAX
Worse Result Count :=
CALCULATE (
    COUNTROWS ( 'Fact Provider Measure' ),
    'Fact Provider Measure'[Comparison Category]
        IN {
            "Worse than national rate",
            "Worse than expected",
            "More days than average"
        }
)
```

These counts use CMS-published categories. They are not a project-created
ranking or grade.

## HRRP

```DAX
Selected HRRP Excess Ratio :=
IF (
    SELECTEDVALUE ( 'Fact HRRP'[Is Reportable] ) = TRUE (),
    SELECTEDVALUE ( 'Fact HRRP'[Excess Readmission Ratio] ),
    BLANK ()
)
```

```DAX
HRRP Above Expected Count :=
CALCULATE (
    COUNTROWS ( 'Fact HRRP' ),
    'Fact HRRP'[Is Reportable] = TRUE (),
    'Fact HRRP'[Excess Readmission Ratio] > 1
)
```

This uses the official published excess readmission ratio. It does not
recalculate HRRP or payment adjustments.

## HVBP

```DAX
Selected HVBP TPS :=
IF (
    SELECTEDVALUE ( 'Fact HVBP'[TPS Reportable] ) = TRUE (),
    SELECTEDVALUE ( 'Fact HVBP'[Total Performance Score] ),
    BLANK ()
)
```

No domain or TPS score is summed across facilities.

## Data quality

```DAX
Passed QA Checks :=
CALCULATE (
    COUNTROWS ( 'Fact Quality Check' ),
    'Fact Quality Check'[Status] = "PASS"
)
```

```DAX
Failed QA Checks :=
CALCULATE (
    COUNTROWS ( 'Fact Quality Check' ),
    'Fact Quality Check'[Status] = "FAIL"
)
```

The Data Quality page must show phase and severity filters so a total pass
count is never presented without scope.

