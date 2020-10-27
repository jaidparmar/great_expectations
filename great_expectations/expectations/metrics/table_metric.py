import logging
from functools import wraps
from typing import Any, Callable, Dict, Tuple, Type

import sqlalchemy as sa

from great_expectations.execution_engine import (
    ExecutionEngine,
    PandasExecutionEngine,
    SparkDFExecutionEngine,
)
from great_expectations.execution_engine.sqlalchemy_execution_engine import (
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.metric_provider import (
    MetricProvider,
    metric,
)

logger = logging.getLogger(__name__)

try:
    import pyspark.sql.functions as F
    import pyspark.sql.types as sparktypes
    from pyspark.ml.feature import Bucketizer
    from pyspark.sql import DataFrame, SQLContext, Window
    from pyspark.sql.functions import (
        array,
        col,
        count,
        countDistinct,
        datediff,
        desc,
        expr,
        isnan,
        lag,
    )
    from pyspark.sql.functions import length as length_
    from pyspark.sql.functions import (
        lit,
        monotonically_increasing_id,
        stddev_samp,
        udf,
        when,
        year,
    )

except ImportError as e:
    logger.debug(str(e))
    logger.debug(
        "Unable to load spark context; install optional spark dependency for support."
    )


def aggregate_metric(engine: Type[ExecutionEngine], **kwargs):
    """Return the aggregate metric decorator for the specified engine.

    Args:
        engine:
        **kwargs:

    Returns:

    """
    if issubclass(engine, PandasExecutionEngine):

        def wrapper(metric_fn: Callable):
            @metric(engine=PandasExecutionEngine, metric_fn_type="data")
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: "PandasExecutionEngine",
                metric_domain_kwargs: dict,
                metric_value_kwargs: dict,
                metrics: Dict[Tuple, Any],
                runtime_configuration: dict,
            ):
                df, _, _ = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs,
                )
                return metric_fn(cls, df, **metric_value_kwargs, _metrics=metrics,)

            return inner_func

        return wrapper

    elif issubclass(engine, SqlAlchemyExecutionEngine):

        def wrapper(metric_fn: Callable):
            @metric(engine=SqlAlchemyExecutionEngine, metric_fn_type="aggregate_fn")
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: "SqlAlchemyExecutionEngine",
                metric_domain_kwargs: dict,
                metric_value_kwargs: dict,
                metrics: Dict[Tuple, Any],
                runtime_configuration: dict,
            ):
                (
                    selectable,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(metric_domain_kwargs)
                dialect = execution_engine.dialect
                sqlalchemy_engine = execution_engine.engine
                metric_aggregate = metric_fn(
                    cls,
                    selectable,
                    **metric_value_kwargs,
                    _dialect=dialect,
                    _table=selectable,
                    _sqlalchemy_engine=sqlalchemy_engine,
                    _metrics=metrics,
                )
                return metric_aggregate, compute_domain_kwargs

            return inner_func

        return wrapper

    elif issubclass(engine, SparkDFExecutionEngine):

        def wrapper(metric_fn: Callable):
            @metric(engine=SparkDFExecutionEngine, metric_fn_type="aggregate_fn")
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: "SparkDFExecutionEngine",
                metric_domain_kwargs: dict,
                metric_value_kwargs: dict,
                metrics: Dict[Tuple, Any],
                runtime_configuration: dict,
            ):
                (
                    data,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs
                )
                metric_aggregate = metric_fn(
                    cls, data, **metric_value_kwargs, _metrics=metrics,
                )
                return metric_aggregate, compute_domain_kwargs

            return inner_func

        return wrapper

    else:
        raise ValueError("Unsupported engine for aggregate_metric")


class AggregateMetricProvider(MetricProvider):
    domain_keys = (
        "batch_id",
        "table",
    )
    metric_fn_type = "aggregate_fn"
