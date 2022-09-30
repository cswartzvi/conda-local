import logging
import sys
from typing import Any, Callable

import click
import yaml

from conda_replicate.adapters.subdir import get_default_subdirs
from conda_replicate.adapters.subdir import get_known_subdirs
from conda_replicate.api import LATEST
from conda_replicate.cli.state import AppState
from conda_replicate.cli.state import ConfigurationState

_DEFAULT_SUBDIRS = get_default_subdirs()
_ALLOWED_SUBDIRS = [subdir for subdir in sorted(get_known_subdirs())]


def channel_option(function: Callable):
    """Decorator for the `channel` option. Not exposed to the underlying command."""

    def callback(context: click.Context, parameter: click.Parameter, value: Any):
        state = context.ensure_object(AppState)
        if value:
            state.channel = value
        return state.channel

    return click.option(
        "-c",
        "--channel",
        "channel",
        type=click.types.STRING,
        callback=callback,
        show_default=True,
        expose_value=False,  # Must be False
        is_eager=False,  # Must be False
        help=(
            "Upstream anaconda channel. Can be specified using the canonical channel "
            "name on anaconda.org (conda-forge), a fully qualified URL "
            "(https://conda.anaconda.org/conda-forge/), or a local directory path."
        ),
    )(function)


def configuration_option(function):
    """Decorator for the `config` option. Not exposed to the underlying command."""

    def callback(context: click.Context, parameter: click.Parameter, value: Any):
        state = context.ensure_object(AppState)
        if value:
            with open(value, "rt") as file:
                contents = yaml.load(file, Loader=yaml.CLoader)
                configuration = ConfigurationState.parse_obj(contents)

            for name in configuration.__fields_set__:
                setattr(state, name, getattr(configuration, name))
        return value

    return click.option(
        "--config",
        default=None,
        type=click.types.Path(exists=True, file_okay=True, dir_okay=False),
        callback=callback,
        expose_value=False,  # Must be False
        is_eager=True,  # Must be True
        help="Path to the yaml configuration file.",
    )(function)


def debug_option(function: Callable):
    """
    Decorator for the `quiet` command line option.  Not exposed underlying command.

    The `debug` option prints debugging information to stdout. Should force the
    quiet command to a matching value.
    """

    def callback(context: click.Context, parameter: click.Parameter, value: Any):
        state = context.ensure_object(AppState)
        if value is not None:
            state.debug = value
        if state.debug:
            logging.basicConfig(
                format="%(filename)s: %(message)s",
                stream=sys.stdout,
                level=logging.DEBUG,
            )
            state.quiet = True  # no animation / progress in debug mode
        return state.debug

    return click.option(
        "-d",
        "--debug",
        is_flag=True,
        default=None,  # Must be None
        callback=callback,
        expose_value=False,  # Must be False
        is_eager=False,  # Must be False
        help="Enable debugging output. Automatically enters quiet mode.",
    )(function)


def exclusions_option(function: Callable):
    """Decorator for the `exclude` option. Not exposed to the underlying command.

    Options specified on the command line are added to 'exclusions` list in the
    configuration file.
    """

    def callback(context: click.Context, parameter: click.Parameter, value: Any):
        state = context.ensure_object(AppState)
        if value:
            state.exclusions.update(value)
        return state.exclusions

    return click.option(
        "--exclude",
        "exclusions",
        multiple=True,
        type=click.types.STRING,
        callback=callback,
        expose_value=False,  # Must be False
        is_eager=False,  # Must be False
        help=(
            "Packages excluded from the search process. Specified using the anaconda "
            "package query syntax. Multiple options may be passed at one time. "
        ),
    )(function)


def disposables_option(function: Callable):
    """Decorator for the `dispose` option. Not exposed to the underlying command.

    Options specified on the command line are added to 'disposables` list in the
    configuration file.
    """

    def callback(context: click.Context, parameter: click.Parameter, value: Any):
        state = context.ensure_object(AppState)
        if value:
            state.disposables.update(value)
        return state.disposables

    return click.option(
        "--dispose",
        "disposables",
        multiple=True,
        type=click.types.STRING,
        callback=callback,
        expose_value=False,  # Must be False
        is_eager=False,  # Must be False
        help=(
            "Packages that are used in the search process but not included in the "
            "final results. Specified using the anaconda package query syntax. "
            "Multiple options may be passed at one time. "
        ),
    )(function)


def latest_option(function: Callable):
    """Decorator for the `latest` option. Not exposed to the underlying command."""

    def callback(context: click.Context, parameter: click.Parameter, value: Any):
        state = context.ensure_object(AppState)
        if value is not None:
            state.latest = value
        return state.latest

    return click.option(
        "--latest",
        type=click.types.Choice(LATEST),
        default=None,
        callback=callback,
        metavar="CRIT",
        expose_value=False,  # Must be False
        is_eager=False,  # Must be False
        help=(
            f"Only query the latest packages using the specified criteria. By default "
            "this only applies to dependencies (see --latest-root). "
            f"Allowed values: {{{', '.join(LATEST)}}}."
        ),
    )(function)


def latest_roots_option(function: Callable):
    """Decorator for the `latest-roots` option. Not exposed to the underlying
    command."""

    def callback(context: click.Context, parameter: click.Parameter, value: Any):
        state = context.ensure_object(AppState)
        if value is not None:
            state.latest_roots = value
        return state.latest_roots

    return click.option(
        "--latest-roots",
        is_flag=True,
        default=False,  # Must be None
        callback=callback,
        expose_value=False,  # Must be False
        is_eager=False,  # Must be False
        help=(
            "Applies latest criteria to root packages. Ignored if --latest is not "
            "specified."
        ),
    )(function)


def quiet_option(function: Callable):
    """Decorator for the `quiet` option. Not exposed to the underlying command."""

    def callback(context: click.Context, parameter: click.Parameter, value: Any):
        state = context.ensure_object(AppState)
        if value is not None:
            state.quiet = value
        if state.debug:
            state.quiet = False
        return state.quiet

    return click.option(
        "--quiet",
        is_flag=True,
        default=None,  # Must be None
        callback=callback,
        expose_value=False,  # Must be False
        is_eager=False,  # Must be False
        help="Quite mode. Suppresses all animations and status related output.",
    )(function)


def requirements_argument(function: Callable):
    def callback(context: click.Context, parameter: click.Parameter, value: Any):
        state = context.ensure_object(AppState)
        if value:
            state.requirements.update(value)
        if not state.requirements:
            raise click.BadParameter("Missing option")
        return state.requirements

    return click.argument(
        "requirements",
        nargs=-1,
        type=click.types.STRING,
        callback=callback,
        is_eager=False,  # Must be False
        expose_value=False,  # Must be False
    )(function)


def subdirs_option(function: Callable):
    """Decorator for the `subdirs` option. Not exposed to the underlying command.

    Options specified on the command line are added to 'subdirs` list in the
    configuration file.
    """

    def callback(context: click.Context, parameter: click.Parameter, value: Any):
        state = context.ensure_object(AppState)
        if value:
            state.subdirs.update(value)
        return state.subdirs

    return click.option(
        "--subdir",
        "subdirs",
        multiple=True,
        type=click.types.Choice(_ALLOWED_SUBDIRS),
        callback=callback,
        default=_DEFAULT_SUBDIRS,
        metavar="SUBDIR",
        show_default=True,
        expose_value=False,  # Must be False
        is_eager=False,  # Must be False
        help=(
            "Selected platform sub-directories. Multiple options may be passed at "
            f"one time. Allowed values: {{{', '.join(_ALLOWED_SUBDIRS)}}}."
        ),
    )(function)


def target_callback(context: click.Context, parameter: click.Parameter, value: Any):
    """Callback function for `target` options."""
    state = context.ensure_object(AppState)
    if value:
        state.target = value
    return state.target
