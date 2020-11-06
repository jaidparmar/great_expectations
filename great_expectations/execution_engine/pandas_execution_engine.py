import copy
import datetime
import logging
from functools import partial
from io import StringIO
import hashlib
import random
from typing import Any, Callable, Dict, Iterable, Tuple, List

import pandas as pd

from great_expectations.execution_environment.types import PathBatchSpec, S3BatchSpec, InMemoryBatchSpec

from ..core.batch import Batch, BatchMarkers, BatchRequest
from ..core.id_dict import BatchSpec
from ..exceptions import BatchSpecError, ValidationError
from ..execution_environment.util import hash_pandas_dataframe
from ..validator.validation_graph import MetricConfiguration
from .execution_engine import ExecutionEngine

logger = logging.getLogger(__name__)

HASH_THRESHOLD = 1e9


class PandasExecutionEngine(ExecutionEngine):
    """
PandasExecutionEngine instantiates the great_expectations Expectations API as a subclass of a pandas.DataFrame.

For the full API reference, please see :func:`Dataset <great_expectations.data_asset.dataset.Dataset>`

Notes:
    1. Samples and Subsets of PandaDataSet have ALL the expectations of the original \
       data frame unless the user specifies the ``discard_subset_failing_expectations = True`` \
       property on the original data frame.
    2. Concatenations, joins, and merges of PandaDataSets contain NO expectations (since no autoinspection
       is performed by default).

--ge-feature-maturity-info--

    id: validation_engine_pandas
    title: Validation Engine - Pandas
    icon:
    short_description: Use Pandas DataFrame to validate data
    description: Use Pandas DataFrame to validate data
    how_to_guide_url:
    maturity: Production
    maturity_details:
        api_stability: Stable
        implementation_completeness: Complete
        unit_test_coverage: Complete
        integration_infrastructure_test_coverage: N/A -> see relevant Datasource evaluation
        documentation_completeness: Complete
        bug_risk: Low
        expectation_completeness: Complete

--ge-feature-maturity-info--
    """

    recognized_batch_spec_defaults = {
        "reader_method",
        "reader_options",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.discard_subset_failing_expectations = kwargs.get(
            "discard_subset_failing_expectations", False
        )

    def configure_validator(self, validator):
        super().configure_validator(validator)
        validator.expose_dataframe_methods = True
        
    # TODO: <Alex>Is this method still needed?  The method "get_batch_data_and_markers()" seems to accoplish the needed functionality.</Alex>
    def load_batch(self, batch_spec: BatchSpec = None) -> Batch:
        """
        Utilizes the provided batch spec to load a batch using the appropriate file reader and the given file path.
        :arg batch_spec the parameters used to build the batch
        :returns Batch
        """
        batch_spec._id_ignore_keys = {"dataset"}
        batch_id = batch_spec.to_id()

        # We need to build a batch_markers to be used in the dataframe
        batch_markers = BatchMarkers(
            {
                "ge_load_time": datetime.datetime.now(datetime.timezone.utc).strftime(
                    "%Y%m%dT%H%M%S.%fZ"
                )
            }
        )

        if isinstance(batch_spec, InMemoryBatchSpec):
            # We do not want to store the actual dataframe in batch_spec (mark that this is PandasInMemoryDF instead).
            batch_data = batch_spec.pop("batch_data")
            batch_spec["PandasInMemoryDF"] = True
            if batch_data is not None:
                if batch_spec.get("data_asset_name"):
                    df = batch_data
                else:
                    raise ValueError("To pass an batch_data, you must also a data_asset_name as well.")
        else:
            reader_method = batch_spec.get("reader_method")
            reader_options = batch_spec.get("reader_options") or {}
            if isinstance(batch_spec, PathBatchSpec):
                path = batch_spec["path"]
                reader_fn = self._get_reader_fn(reader_method, path)
                df = reader_fn(path, **reader_options)
            elif isinstance(batch_spec, S3BatchSpec):
                # TODO: <Alex>The job of S3DataConnector is to supply the URL and the S3_OBJECT (like FilesystemDataConnector supplies the PATH).</Alex>
                # TODO: <Alex>Move the code below to S3DataConnector (which will update batch_spec with URL and S3_OBJECT values.</Alex>
                # url, s3_object = data_connector.get_s3_object(batch_spec=batch_spec)
                # reader_method = batch_spec.get("reader_method")
                # reader_fn = self._get_reader_fn(reader_method, url.key)
                # df = reader_fn(
                #     StringIO(
                #         s3_object["Body"]
                #         .read()
                #         .decode(s3_object.get("ContentEncoding", "utf-8"))
                #     ),
                #     **reader_options,
                # )
                pass
            else:
                raise BatchSpecError(
                    "Invalid batch_spec: file path, s3 path, or df is required for a PandasExecutionEngine to operate."
                )

        if df.memory_usage().sum() < HASH_THRESHOLD:
            batch_markers["pandas_data_fingerprint"] = hash_pandas_dataframe(df)

        if not self.batches.get(batch_id) or self.batches.get(batch_id).batch_spec != batch_spec:
            batch = Batch(
                data=df,
                batch_spec=batch_spec,
                batch_markers=batch_markers,
            )
            self.batches[batch_id] = batch
        else:
            batch = self.batches.get(batch_id)

        self._loaded_batch_id = batch_id
        return batch
    
    def get_batch_data(
        self,
        batch_spec: BatchSpec,
    ) -> Any :
        """Interprets batch_data and returns the appropriate data.

        This method is primarily useful for utility cases (e.g. testing) where
        data is being fetched without a DataConnector and metadata like
        batch_markers is unwanted

        Note: this method is currently a thin wrapper for get_batch_data_and_markers.
        It simply suppresses the batch_markers.
        """
        batch_data, _ = self.get_batch_data_and_markers(batch_spec)
        return batch_data

    def get_batch_data_and_markers(
        self,
        batch_spec: BatchSpec
    ) -> Tuple[
        Any,  # batch_data
        BatchMarkers
    ]:
        batch_data: Any = None

        # We need to build a batch_markers to be used in the dataframe
        batch_markers: BatchMarkers = BatchMarkers(
            {
                "ge_load_time": datetime.datetime.now(datetime.timezone.utc).strftime(
                    "%Y%m%dT%H%M%S.%fZ"
                )
            }
        )

        if isinstance(batch_spec, InMemoryBatchSpec):
            batch_data = batch_spec.dataset

        elif isinstance(batch_spec, PathBatchSpec):
            reader_method: str = batch_spec.get("reader_method")
            reader_options: dict = batch_spec.get("reader_options") or {}

            path: str = batch_spec["path"]
            reader_fn: Callable = self._get_reader_fn(reader_method, path)

            batch_data = reader_fn(path, **reader_options)

        elif isinstance(batch_spec, S3BatchSpec):
            # TODO: <Alex>The job of S3DataConnector is to supply the URL and the S3_OBJECT (like FilesystemDataConnector supplies the PATH).</Alex>
            # TODO: <Alex>Move the code below to S3DataConnector (which will update batch_spec with URL and S3_OBJECT values.</Alex>
            # url, s3_object = data_connector.get_s3_object(batch_spec=batch_spec)
            # reader_method = batch_spec.get("reader_method")
            # reader_fn = self._get_reader_fn(reader_method, url.key)
            # batch_data = reader_fn(
            #     StringIO(
            #         s3_object["Body"]
            #         .read()
            #         .decode(s3_object.get("ContentEncoding", "utf-8"))
            #     ),
            #     **reader_options,
            # )
            pass
        else:
            raise BatchSpecError(
                """Invalid batch_spec: file path, s3 path, or batch_data is required for a PandasExecutionEngine to
operate.
                """
            )

        splitter_method: str = batch_spec.get("splitter_method") or None
        splitter_kwargs: str = batch_spec.get("splitter_kwargs") or {}
        if splitter_method:
            splitter_fn = getattr(self, splitter_method)
            batch_data = splitter_fn(batch_data, **splitter_kwargs)

        sampling_method: str = batch_spec.get("sampling_method") or None
        sampling_kwargs: str = batch_spec.get("sampling_kwargs") or {}
        if sampling_method:
            sampling_fn = getattr(self, sampling_method)
            batch_data = sampling_fn(batch_data, **sampling_kwargs)

        if batch_data is not None:
            if batch_data.memory_usage().sum() < HASH_THRESHOLD:
                batch_markers["pandas_data_fingerprint"] = hash_pandas_dataframe(batch_data)

        return batch_data, batch_markers

    @staticmethod
    def get_batch_markers_and_update_batch_spec_for_batch_data(
        batch_data: pd.DataFrame,
        batch_spec: BatchSpec
    ) -> BatchMarkers:
        """
        Computes batch_markers in the case of user-provided batch_data (e.g., in the case of a data pipeline).

        :param batch_data -- user-provided dataframe
        :param batch_spec -- BatchSpec (must be previously instantiated/initialized by RuntimeDataConnector)
        :returns computed batch_markers specific to this execution engine
        """
        batch_markers: BatchMarkers = BatchMarkers(
            {
                "ge_load_time": datetime.datetime.now(datetime.timezone.utc).strftime(
                    "%Y%m%dT%H%M%S.%fZ"
                )
            }
        )
        if batch_data is not None:
            if batch_data.memory_usage().sum() < HASH_THRESHOLD:
                batch_markers["pandas_data_fingerprint"] = hash_pandas_dataframe(batch_data)
            # we do not want to store the actual dataframe in batch_spec
            # hence, marking that this is a PandasInMemoryDF instead
            batch_spec["PandasInMemoryDF"] = True
        return batch_markers

    @property
    def dataframe(self):
        """Tests whether or not a Batch has been loaded. If the loaded batch does not exist, raises a
        ValueError Exception
        """
        if not self.active_batch_data:
            raise ValueError(
                "Batch has not been loaded - please run load_batch() to load a batch."
            )

        return self.active_batch_data

    def _get_reader_fn(self, reader_method=None, path=None):
        """Static helper for parsing reader types. If reader_method is not provided, path will be used to guess the
        correct reader_method.

        Args:
            reader_method (str): the name of the reader method to use, if available.
            path (str): the path used to guess

        Returns:
            ReaderMethod to use for the filepath

        """
        if reader_method is None and path is None:
            raise BatchSpecError(
                "Unable to determine pandas reader function without reader_method or path."
            )

        reader_options = dict()
        if reader_method is None:
            path_guess = self.guess_reader_method_from_path(path)
            reader_method = path_guess["reader_method"]
            reader_options = path_guess.get(
                "reader_options"
            )  # This may not be there; use None in that case

        try:
            reader_fn = getattr(pd, reader_method)
            if reader_options:
                reader_fn = partial(reader_fn, **reader_options)
            return reader_fn
        except AttributeError:
            raise BatchSpecError(
                f'Unable to find reader_method "{reader_method}" in pandas.'
            )

    # NOTE Abe 20201105: Any reason this shouldn't be a private method?
    @staticmethod
    def guess_reader_method_from_path(path):
        """Helper method for deciding which reader to use to read in a certain path.

               Args:
                   path (str): the to use to guess

               Returns:
                   ReaderMethod to use for the filepath

               """
        if path.endswith(".csv") or path.endswith(".tsv"):
            return {"reader_method": "read_csv"}
        elif path.endswith(".parquet"):
            return {"reader_method": "read_parquet"}
        elif path.endswith(".xlsx") or path.endswith(".xls"):
            return {"reader_method": "read_excel"}
        elif path.endswith(".json"):
            return {"reader_method": "read_json"}
        elif path.endswith(".pkl"):
            return {"reader_method": "read_pickle"}
        elif path.endswith(".feather"):
            return {"reader_method": "read_feather"}
        elif path.endswith(".csv.gz") or path.endswith(".csv.gz"):
            return {
                "reader_method": "read_csv",
                "reader_options": {"compression": "gzip"},
            }

        raise BatchSpecError(f'Unable to determine reader method from path: "{path}".')

    def get_compute_domain(
        self, domain_kwargs: dict,
    ) -> Tuple[pd.DataFrame, dict, dict]:
        """Uses a given batch dictionary and domain kwargs (which include a row condition and a condition parser)
        to obtain and/or query a batch. Returns in the format of a Pandas Series if only a single column is desired,
        or otherwise a Data Frame.

        Args:
            domain_kwargs (dict) - A dictionary consisting of the domain kwargs specifying which data to obtain
            batches (dict) - A dictionary specifying batch id and which batches to obtain

        Returns:
            A tuple including:
              - a DataFrame (the data on which to compute)
              - a dictionary of compute_domain_kwargs, describing the DataFrame
              - a dictionary of accessor_domain_kwargs, describing any accessors needed to
                identify the domain within the compute domain
        """
        batch_id = domain_kwargs.get("batch_id")
        if batch_id is None:
            # We allow no batch id specified if there is only one batch
            if self.active_batch_data_id is not None:
                data = self.active_batch_data
            else:
                raise ValidationError(
                    "No batch is specified, but could not identify a loaded batch."
                )
        else:
            if batch_id in self.loaded_batch_data:
                data = self.loaded_batch_data[batch_id]
            else:
                raise ValidationError(f"Unable to find batch with batch_id {batch_id}")

        compute_domain_kwargs = copy.deepcopy(domain_kwargs)
        accessor_domain_kwargs = dict()
        table = domain_kwargs.get("table", None)
        if table:
            raise ValueError(
                "PandasExecutionEngine does not currently support multiple named tables."
            )

        row_condition = domain_kwargs.get("row_condition", None)
        if row_condition:
            condition_parser = domain_kwargs.get("condition_parser", None)
            if condition_parser not in ["python", "pandas"]:
                raise ValueError(
                    "condition_parser is required when setting a row_condition,"
                    " and must be 'python' or 'pandas'"
                )
            else:
                data = data.query(row_condition, parser=condition_parser).reset_index(
                    drop=True
                )

        if "column" in compute_domain_kwargs:
            accessor_domain_kwargs["column"] = compute_domain_kwargs.pop("column")

        return data, compute_domain_kwargs, accessor_domain_kwargs

    def resolve_metric_bundle(
        self, metric_fn_bundle: Iterable[Tuple[MetricConfiguration, Callable, dict]],
    ) -> dict:
        """This engine simply evaluates metrics one at a time."""
        resolved_metrics = dict()
        for (
            metric_to_resolve,
            metric_provider,
            metric_provider_kwargs,
        ) in metric_fn_bundle:
            resolved_metrics[metric_to_resolve.id] = metric_provider(
                **metric_provider_kwargs
            )
        return resolved_metrics



    ### Splitter methods for partitioning dataframes ###

    @staticmethod
    def _split_on_whole_table(
        df,
    ) -> pd.DataFrame:
        return df

    @staticmethod
    def _split_on_column_value(
        df,
        column_name: str,
        partition_definition: dict,
    ) -> pd.DataFrame:

        return df[df[column_name]==partition_definition[column_name]]

    @staticmethod
    def _split_on_converted_datetime(
        df,
        column_name: str,
        partition_definition: dict,
        date_format_string: str='%Y-%m-%d',
    ):
        """Convert the values in the named column to the given date_format, and split on that"""

        stringified_datetime_series = df[column_name].map(lambda x: x.strftime(date_format_string))
        matching_string = partition_definition[column_name]

        return df[ stringified_datetime_series == matching_string ]

    @staticmethod
    def _split_on_divided_integer(
        df,
        column_name: str,
        divisor:int,
        partition_definition: dict,
    ):
        """Divide the values in the named column by `divisor`, and split on that"""

        matching_divisor = partition_definition[column_name]
        matching_rows = df[column_name].map(lambda x: int(x/divisor)==matching_divisor)

        return df[matching_rows]

    @staticmethod
    def _split_on_mod_integer(
        df,
        column_name: str,
        mod:int,
        partition_definition: dict,
    ):
        """Divide the values in the named column by `divisor`, and split on that"""

        matching_mod_value = partition_definition[column_name]
        matching_rows = df[column_name].map(lambda x: x % mod == matching_mod_value)

        return df[matching_rows]

    @staticmethod
    def _split_on_multi_column_values(
        df,
        column_names: List[str],
        partition_definition: dict,
    ):
        """Split on the joint values in the named columns"""

        subset_df = df.copy()
        for column_name, value in partition_definition.items():
            subset_df = subset_df[subset_df[column_name]==value]

        return subset_df

    @staticmethod
    def _split_on_hashed_column(
        df,
        column_name: str,
        hash_digits: int,
        partition_definition: dict,
    ):
        """Split on the hashed value of the named column"""

        matching_rows = df[column_name].map(
            lambda x: hashlib.md5(str(x).encode()).hexdigest()[-1*hash_digits:] == partition_definition["hash_value"]
        )

        return df[matching_rows]

    ### Sampling methods ###

    @staticmethod
    def _sample_using_random(
        df,
        p: float = .1,
    ):
        """Take a random sample of rows, retaining proportion p
        
        Note: the Random function behaves differently on different dialects of SQL
        """
        return df[df.index.map( lambda x: random.random() < p )]

    @staticmethod
    def _sample_using_mod(
        df,
        column_name: str,
        mod: int,
        value: int,
    ):
        """Take the mod of named column, and only keep rows that match the given value"""
        return df[df[column_name].map( lambda x: x % mod == value)]

    @staticmethod
    def _sample_using_a_list(
        df,
        column_name: str,
        value_list: list,
    ):
        """Match the values in the named column against value_list, and only keep the matches"""
        return df[df[column_name].isin(value_list)]

    @staticmethod
    def _sample_using_md5(
        df,
        column_name: str,
        hash_digits: int=1,
        hash_value: str='f',
    ):
        """Hash the values in the named column, and split on that"""
        matches = df[column_name].map(
            lambda x: hashlib.md5(str(x).encode()).hexdigest()[-1*hash_digits:] == hash_value
        )
        return df[matches]