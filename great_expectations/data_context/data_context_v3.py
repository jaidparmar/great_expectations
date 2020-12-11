import logging
import os
import traceback

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from great_expectations.data_context.data_context import (
    DataContext,
    datasourceConfigSchema,
)
from great_expectations.data_context.types.base import DatasourceConfig
from great_expectations.data_context.util import (
    instantiate_class_from_config,
    substitute_all_config_variables,
)

logger = logging.getLogger(__name__)

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.default_flow_style = False


class DataContextV3(DataContext):
    """Class implementing the v3 spec for DataContext configs, plus API changes for the 0.13+ series."""

    def test_yaml_config(
        self,
        yaml_config: str,
        name=None,
        pretty_print=True,
        return_mode="instantiated_class",
        shorten_tracebacks=False,
    ):
        """ Convenience method for testing yaml configs

        test_yaml_config is a convenience method for configuring the moving
        parts of a Great Expectations deployment. It allows you to quickly
        test out configs for system components, especially Datasources,
        Checkpoints, and Stores.

        For many deployments of Great Expectations, these components (plus
        Expectations) are the only ones you'll need.

        test_yaml_config is mainly intended for use within notebooks and tests.

        Parameters
        ----------
        yaml_config : str
            A string containing the yaml config to be tested

        name: str
            (Optional) A string containing the name of the component to instantiate

        pretty_print : bool
            Determines whether to print human-readable output

        return_mode : str
            Determines what type of object test_yaml_config will return
            Valid modes are "instantiated_class" and "report_object"

        shorten_tracebacks : bool
            If true, catch any errors during instantiation and print only the
            last element of the traceback stack. This can be helpful for
            rapid iteration on configs in a notebook, because it can remove
            the need to scroll up and down a lot.

        Returns
        -------
        The instantiated component (e.g. a Datasource)
        OR
        a json object containing metadata from the component's self_check method

        The returned object is determined by return_mode.
        """
        if pretty_print:
            print("Attempting to instantiate class from config...")

        if return_mode not in ["instantiated_class", "report_object"]:
            raise ValueError(f"Unknown return_mode: {return_mode}.")

        substituted_config_variables = substitute_all_config_variables(
            self.config_variables, dict(os.environ),
        )

        substitutions = {
            **substituted_config_variables,
            **dict(os.environ),
            **self.runtime_environment,
        }

        config_str_with_substituted_variables = substitute_all_config_variables(
            yaml_config, substitutions,
        )

        config = yaml.load(config_str_with_substituted_variables)

        if "class_name" in config:
            class_name = config["class_name"]
        else:
            class_name = None

        try:
            if class_name in [
                "ExpectationsStore",
                "ValidationsStore",
                "HtmlSiteStore",
                "EvaluationParameterStore",
                "MetricStore",
                "SqlAlchemyQueryStore",
            ]:
                print(f"\tInstantiating as a Store, since class_name is {class_name}")
                instantiated_class = self._build_store_from_config(
                    "my_temp_store", config
                )

            elif class_name in [
                "Datasource",
                "SimpleSqlalchemyDatasource",
            ]:
                print(
                    f"\tInstantiating as a Datasource, since class_name is {class_name}"
                )
                datasource_name = name or "my_temp_datasource"
                datasource_config: DatasourceConfig = datasourceConfigSchema.load(
                    CommentedMap(**config)
                )
                self._project_config["datasources"][datasource_name] = datasource_config
                datasource_config = self._project_config_with_variables_substituted.datasources[
                    datasource_name
                ]
                config = dict(datasourceConfigSchema.dump(datasource_config))
                instantiated_class = self._instantiate_datasource_from_config(
                    name=datasource_name, config=config
                )
                self._cached_datasources[datasource_name] = instantiated_class

            else:
                print(
                    "\tNo matching class found. Attempting to instantiate class from the raw config..."
                )
                instantiated_class = instantiate_class_from_config(
                    config, runtime_environment={}, config_defaults={}
                )

            if pretty_print:
                print(
                    f"\tSuccessfully instantiated {instantiated_class.__class__.__name__}"
                )
                print()

            report_object = instantiated_class.self_check(pretty_print)

            if return_mode == "instantiated_class":
                return instantiated_class

            elif return_mode == "report_object":
                return report_object

        except Exception as e:
            if shorten_tracebacks:
                traceback.print_exc(limit=1)
            else:
                raise e
