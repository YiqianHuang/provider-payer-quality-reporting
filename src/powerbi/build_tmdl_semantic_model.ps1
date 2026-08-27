param(
    [Parameter(Mandatory = $false)]
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
)

$ErrorActionPreference = 'Stop'
$projectPath = (Resolve-Path -LiteralPath $ProjectRoot).Path
$specPath = Join-Path $projectPath 'powerbi\semantic_model.json'
$spec = Get-Content -Raw -LiteralPath $specPath | ConvertFrom-Json
$desktopBin = 'C:\Program Files\Microsoft Power BI Desktop\bin'

foreach ($assemblyName in @(
    'Microsoft.PowerBI.Tabular.dll'
)) {
    $assemblyPath = Join-Path $desktopBin $assemblyName
    if (-not (Test-Path -LiteralPath $assemblyPath)) {
        throw "Required Power BI Desktop assembly not found: $assemblyPath"
    }
    [void][System.Reflection.Assembly]::LoadFrom($assemblyPath)
}

function Convert-DataType {
    param([string]$Name)
    switch ($Name) {
        'Text' { return [Microsoft.AnalysisServices.Tabular.DataType]::String }
        'Int64' { return [Microsoft.AnalysisServices.Tabular.DataType]::Int64 }
        'Double' { return [Microsoft.AnalysisServices.Tabular.DataType]::Double }
        'Boolean' { return [Microsoft.AnalysisServices.Tabular.DataType]::Boolean }
        'Date' { return [Microsoft.AnalysisServices.Tabular.DataType]::DateTime }
        'DateTime' { return [Microsoft.AnalysisServices.Tabular.DataType]::DateTime }
        default { throw "Unsupported semantic data type: $Name" }
    }
}

function Convert-MType {
    param([string]$Name)
    switch ($Name) {
        'Text' { return 'type text' }
        'Int64' { return 'Int64.Type' }
        'Double' { return 'type number' }
        'Boolean' { return 'type logical' }
        'Date' { return 'type date' }
        'DateTime' { return 'type datetime' }
        default { throw "Unsupported Power Query data type: $Name" }
    }
}

$database = New-Object Microsoft.AnalysisServices.Tabular.Database
$database.Name = $spec.model_name
$database.ID = 'ProviderQualityPerformance'
$database.CompatibilityLevel = 1600

$model = New-Object Microsoft.AnalysisServices.Tabular.Model
$model.Name = 'Model'
$model.Culture = 'en-US'
$model.DefaultPowerBIDataSourceVersion =
    [Microsoft.AnalysisServices.Tabular.PowerBIDataSourceVersion]::PowerBI_V3
$model.DiscourageImplicitMeasures = $true
$database.Model = $model

foreach ($tableSpec in $spec.tables) {
    $table = New-Object Microsoft.AnalysisServices.Tabular.Table
    $table.Name = $tableSpec.name

    foreach ($columnSpec in $tableSpec.columns) {
        $column = New-Object Microsoft.AnalysisServices.Tabular.DataColumn
        $column.Name = $columnSpec.name
        $column.SourceColumn = $columnSpec.source
        $column.DataType = Convert-DataType $columnSpec.data_type
        if ($columnSpec.PSObject.Properties.Name -contains 'hidden') {
            $column.IsHidden = [bool]$columnSpec.hidden
        }
        if ($columnSpec.PSObject.Properties.Name -contains 'summarize_by') {
            $column.SummarizeBy = switch ($columnSpec.summarize_by) {
                'None' { [Microsoft.AnalysisServices.Tabular.AggregateFunction]::None }
                'Sum' { [Microsoft.AnalysisServices.Tabular.AggregateFunction]::Sum }
                default { throw "Unsupported summarize_by: $($columnSpec.summarize_by)" }
            }
        }
        $table.Columns.Add($column)
    }

    $csvPath = Join-Path $projectPath (
        "data\processed\powerbi_import\$($tableSpec.source_object).csv"
    )
    if (-not (Test-Path -LiteralPath $csvPath)) {
        throw "Power BI import extract not found: $csvPath"
    }
    $escapedPath = $csvPath.Replace('"', '""')
    $typePairs = @()
    foreach ($columnSpec in $tableSpec.columns) {
        $escapedColumn = $columnSpec.source.Replace('"', '""')
        $typePairs += "{`"$escapedColumn`", $(Convert-MType $columnSpec.data_type)}"
    }
    $mExpression = @"
let
    Source = Csv.Document(
        File.Contents("$escapedPath"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]
    ),
    PromotedHeaders = Table.PromoteHeaders(
        Source,
        [PromoteAllScalars=true]
    ),
    TypedColumns = Table.TransformColumnTypes(
        PromotedHeaders,
        {$($typePairs -join ', ')},
        "en-US"
    )
in
    TypedColumns
"@
    $partition = New-Object Microsoft.AnalysisServices.Tabular.Partition
    $partition.Name = $tableSpec.name
    $partition.Mode = [Microsoft.AnalysisServices.Tabular.ModeType]::Import
    $partitionSource =
        New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource
    $partitionSource.Expression = $mExpression
    $partition.Source = $partitionSource
    $table.Partitions.Add($partition)
    $model.Tables.Add($table)
}

foreach ($measureSpec in $spec.measures) {
    $table = $model.Tables.Find($measureSpec.home_table)
    if ($null -eq $table) {
        throw "Measure home table not found: $($measureSpec.home_table)"
    }
    $measure = New-Object Microsoft.AnalysisServices.Tabular.Measure
    $measure.Name = $measureSpec.name
    $measure.Expression = $measureSpec.expression
    $measure.FormatString = $measureSpec.format_string
    $table.Measures.Add($measure)
}

foreach ($relationshipSpec in $spec.relationships) {
    $oneTable = $model.Tables.Find($relationshipSpec.from_table)
    $manyTable = $model.Tables.Find($relationshipSpec.to_table)
    $relationship =
        New-Object Microsoft.AnalysisServices.Tabular.SingleColumnRelationship
    $relationship.Name = $relationshipSpec.name
    $relationship.FromColumn =
        $manyTable.Columns.Find($relationshipSpec.to_column)
    $relationship.ToColumn =
        $oneTable.Columns.Find($relationshipSpec.from_column)
    $relationship.FromCardinality =
        [Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::Many
    $relationship.ToCardinality =
        [Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::One
    $relationship.CrossFilteringBehavior =
        [Microsoft.AnalysisServices.Tabular.CrossFilteringBehavior]::OneDirection
    $relationship.IsActive = [bool]$relationshipSpec.active
    $model.Relationships.Add($relationship)
}

$semanticFolder = Join-Path $projectPath 'powerbi\ProviderQuality.SemanticModel'
$definitionFolder = Join-Path $semanticFolder 'definition'
$resolvedParent = [IO.Path]::GetFullPath($semanticFolder)
if (-not $resolvedParent.StartsWith(
    [IO.Path]::GetFullPath((Join-Path $projectPath 'powerbi')),
    [StringComparison]::OrdinalIgnoreCase
)) {
    throw "Refusing to replace an output outside the Power BI project folder."
}
if (Test-Path -LiteralPath $definitionFolder) {
    Remove-Item -LiteralPath $definitionFolder -Recurse -Force
}
New-Item -ItemType Directory -Path $definitionFolder -Force | Out-Null

[Microsoft.AnalysisServices.Tabular.TmdlSerializer]::SerializeDatabaseToFolder(
    $database,
    $definitionFolder
)
$roundTrip =
    [Microsoft.AnalysisServices.Tabular.TmdlSerializer]::DeserializeDatabaseFromFolder(
        $definitionFolder
    )

$validation = [ordered]@{
    model_name = $roundTrip.Name
    compatibility_level = $roundTrip.CompatibilityLevel
    table_count = $roundTrip.Model.Tables.Count
    relationship_count = $roundTrip.Model.Relationships.Count
    measure_count = (
        $roundTrip.Model.Tables |
            ForEach-Object { $_.Measures.Count } |
            Measure-Object -Sum
    ).Sum
    expected_table_count = $spec.tables.Count
    expected_relationship_count = $spec.relationships.Count
    expected_measure_count = $spec.measures.Count
    status = 'PASS'
}
if (
    $validation.table_count -ne $validation.expected_table_count -or
    $validation.relationship_count -ne $validation.expected_relationship_count -or
    $validation.measure_count -ne $validation.expected_measure_count
) {
    $validation.status = 'FAIL'
}

$validationPath = Join-Path $projectPath 'outputs\powerbi\tmdl_validation.json'
$validation | ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath $validationPath -Encoding utf8
$validation | ConvertTo-Json -Depth 5
if ($validation.status -ne 'PASS') {
    exit 1
}
