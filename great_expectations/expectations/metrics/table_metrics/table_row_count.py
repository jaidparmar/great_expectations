from great_expectations.execution_engine import (
    PandasExecutionEngine,
    SparkDFExecutionEngine,
)
from great_expectations.execution_engine.sqlalchemy_execution_engine import (
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.column_aggregate_metric import sa as sa
from great_expectations.expectations.metrics.table_metric import (
    TableMetricProvider,
    table_metric,
)


class TableRowCount(TableMetricProvider):
    metric_name = "table.row_count"

    @table_metric(engine=PandasExecutionEngine)
    def _pandas(cls, table, **kwargs):
        return table.shape[0]

    @table_metric(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(cls, table, **kwargs):
        return sa.func.count()

    @table_metric(engine=SparkDFExecutionEngine)
    def _spark(cls, table, **kwargs):
        return table.count()
