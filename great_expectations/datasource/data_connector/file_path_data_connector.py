import logging
from typing import Iterator, List, Optional

import great_expectations.exceptions as ge_exceptions
from great_expectations.core.batch import BatchDefinition, BatchRequest
from great_expectations.datasource.data_connector.data_connector import DataConnector
from great_expectations.datasource.data_connector.partition_query import (
    PartitionQuery,
    build_partition_query,
)
from great_expectations.datasource.data_connector.sorter import Sorter
from great_expectations.datasource.data_connector.util import (
    batch_definition_matches_batch_request,
    build_sorters_from_config,
    map_batch_definition_to_data_reference_string_using_regex,
    map_data_reference_string_to_batch_definition_list_using_regex,
)
from great_expectations.datasource.types import PathBatchSpec
from great_expectations.execution_engine import ExecutionEngine

logger = logging.getLogger(__name__)


class FilePathDataConnector(DataConnector):
    def __init__(
        self,
        name: str,
        datasource_name: str,
        execution_engine: Optional[ExecutionEngine] = None,
        default_regex: Optional[dict] = None,
        sorters: Optional[list] = None,
    ):
        logger.debug(f'Constructing FilePathDataConnector "{name}".')

        super().__init__(
            name=name,
            datasource_name=datasource_name,
            execution_engine=execution_engine,
        )

        if default_regex is None:
            default_regex = {}
        self._default_regex = default_regex

        self._sorters = build_sorters_from_config(config_list=sorters)
        self._validate_sorters_configuration()

    @property
    def sorters(self) -> Optional[dict]:
        return self._sorters

    def _get_data_reference_list_from_cache_by_data_asset_name(
        self, data_asset_name: str
    ) -> List[str]:
        """
        Fetch data_references corresponding to data_asset_name from the cache.
        """
        regex_config: dict = self._get_regex_config(data_asset_name=data_asset_name)
        pattern: str = regex_config["pattern"]
        group_names: List[str] = regex_config["group_names"]

        batch_definition_list = self.get_batch_definition_list_from_batch_request(
            batch_request=BatchRequest(
                datasource_name=self.datasource_name,
                data_connector_name=self.name,
                data_asset_name=data_asset_name,
            )
        )

        path_list: List[str] = [
            map_batch_definition_to_data_reference_string_using_regex(
                batch_definition=batch_definition,
                regex_pattern=pattern,
                group_names=group_names,
            )
            for batch_definition in batch_definition_list
        ]

        # TODO: Sort with a real sorter here
        path_list.sort()

        return path_list

    def get_batch_definition_list_from_batch_request(
        self, batch_request: BatchRequest,
    ) -> List[BatchDefinition]:
        self._validate_batch_request(batch_request=batch_request)

        if self._data_references_cache is None:
            self._refresh_data_references_cache()

        batch_definition_list: List[BatchDefinition] = list(
            filter(
                lambda batch_definition: batch_definition_matches_batch_request(
                    batch_definition=batch_definition, batch_request=batch_request
                ),
                self._get_batch_definition_list_from_cache(),
            )
        )

        if batch_request.partition_request is not None:
            partition_query_obj: PartitionQuery = build_partition_query(
                partition_request_dict=batch_request.partition_request
            )
            batch_definition_list = partition_query_obj.select_from_partition_request(
                batch_definition_list=batch_definition_list
            )

        if len(self.sorters) > 0:
            sorted_batch_definition_list = self._sort_batch_definition_list(
                batch_definition_list=batch_definition_list
            )
            return sorted_batch_definition_list
        else:
            return batch_definition_list

    def _sort_batch_definition_list(
        self, batch_definition_list
    ) -> List[BatchDefinition]:
        sorters: Iterator[Sorter] = reversed(list(self.sorters.values()))
        for sorter in sorters:
            batch_definition_list = sorter.get_sorted_batch_definitions(
                batch_definitions=batch_definition_list
            )
        return batch_definition_list

    def _map_data_reference_to_batch_definition_list(
        self, data_reference: str, data_asset_name: str = None
    ) -> Optional[List[BatchDefinition]]:
        regex_config: dict = self._get_regex_config(data_asset_name=data_asset_name)
        pattern: str = regex_config["pattern"]
        group_names: List[str] = regex_config["group_names"]
        return map_data_reference_string_to_batch_definition_list_using_regex(
            datasource_name=self.datasource_name,
            data_connector_name=self.name,
            data_asset_name=data_asset_name,
            data_reference=data_reference,
            regex_pattern=pattern,
            group_names=group_names,
        )

    def _map_batch_definition_to_data_reference(
        self, batch_definition: BatchDefinition
    ) -> str:
        data_asset_name: str = batch_definition.data_asset_name
        regex_config: dict = self._get_regex_config(data_asset_name=data_asset_name)
        pattern: str = regex_config["pattern"]
        group_names: List[str] = regex_config["group_names"]
        return map_batch_definition_to_data_reference_string_using_regex(
            batch_definition=batch_definition,
            regex_pattern=pattern,
            group_names=group_names,
        )

    def build_batch_spec(self, batch_definition: BatchDefinition) -> PathBatchSpec:
        batch_spec = super().build_batch_spec(batch_definition=batch_definition)
        return PathBatchSpec(batch_spec)

    def _generate_batch_spec_parameters_from_batch_definition(
        self, batch_definition: BatchDefinition
    ) -> dict:
        path: str = self._map_batch_definition_to_data_reference(
            batch_definition=batch_definition
        )
        if not path:
            raise ValueError(
                f"""No data reference for data asset name "{batch_definition.data_asset_name}" matches the given
partition definition {batch_definition.partition_definition} from batch definition {batch_definition}.
                """
            )
        path = self._get_full_file_path(
            path=path, data_asset_name=batch_definition.data_asset_name
        )
        return {"path": path}

    def _validate_batch_request(self, batch_request: BatchRequest):
        super()._validate_batch_request(batch_request)
        self._validate_sorters_configuration(
            data_asset_name=batch_request.data_asset_name
        )

    def _validate_sorters_configuration(self, data_asset_name: Optional[str] = None):
        if self.sorters is not None and len(self.sorters) > 0:
            # data_asset_name: str = batch_request.data_asset_name
            regex_config: dict = self._get_regex_config(data_asset_name=data_asset_name)
            group_names: List[str] = regex_config["group_names"]
            if any(
                [sorter_name not in group_names for sorter_name in self.sorters.keys()]
            ):
                raise ge_exceptions.DataConnectorError(
                    f"""DataConnector "{self.name}" specifies one or more sort keys that do not appear among the
configured group_name.
                    """
                )
            if len(group_names) < len(self.sorters):
                raise ge_exceptions.DataConnectorError(
                    f"""DataConnector "{self.name}" is configured with {len(group_names)} group names;
this is fewer than number of sorters specified, which is {len(self.sorters)}.
                    """
                )

    def _get_batch_definition_list_from_cache(self) -> List[BatchDefinition]:
        raise NotImplementedError

    def _get_regex_config(self, data_asset_name: Optional[str] = None) -> dict:
        raise NotImplementedError

    def _get_full_file_path(
        self, path: str, data_asset_name: Optional[str] = None
    ) -> str:
        raise NotImplementedError
