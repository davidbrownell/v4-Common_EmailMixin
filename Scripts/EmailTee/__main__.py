# ----------------------------------------------------------------------
# |
# |  __main__.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2022-12-11 19:34:49
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2022
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Writes output to stdout, a verbose output file, and a file suitable to email."""

import re
import sys

from io import StringIO
from pathlib import Path
from typing import List

import typer

from typer.core import TyperGroup

from Common_Foundation.ContextlibEx import ExitStack
from Common_Foundation import PathEx
from Common_Foundation.Streams.Capabilities import Capabilities
from Common_Foundation.Streams.StreamDecorator import StreamDecorator
from Common_Foundation import SubprocessEx


sys.path.insert(0, str(PathEx.EnsureDir(Path(__file__).parent / "Impl")))
with ExitStack(lambda: sys.path.pop(0)):
    from ansi2html import Ansi2HTMLConverter  # type: ignore  # pylint: disable=import-error


# ----------------------------------------------------------------------
class NaturalOrderGrouper(TyperGroup):
    # ----------------------------------------------------------------------
    def list_commands(self, *args, **kwargs):  # pylint: disable=unused-argument
        return self.commands.keys()


# ----------------------------------------------------------------------
app                                         = typer.Typer(
    cls=NaturalOrderGrouper,
    help=__doc__,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=False,
)


# ----------------------------------------------------------------------
@app.command("Execute", no_args_is_help=True)
def Execute(
    verbose_output_filename: Path=typer.Argument(..., exists=False, dir_okay=False, resolve_path=True, help="BugBug"),
    html_output_filename: Path=typer.Argument(..., exists=False, dir_okay=False, resolve_path=True, help="BugBug"),
    command_line_args: List[str]=typer.Argument(..., help="BugBug"),
) -> None:
    """Writes output to stdout, a verbose output file, and a file suitable to email."""

    sink = StringIO()

    stream = Capabilities.Alter(
        StreamDecorator([sys.stdout, sink]),
        is_interactive=False,
        supports_colors=True,
        is_headless=True,
    )[0]

    result = SubprocessEx.Stream(
        " ".join('"{}"'.format(command_line_arg) for command_line_arg in command_line_args),
        stream,  # type: ignore
    )

    sink = sink.getvalue()

    # Remove the escape sequences in the verbose output
    verbose_output = re.sub(r"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]", "", sink)

    # Generate the html output
    html_output = Ansi2HTMLConverter().convert(sink)

    # BugBug: Remove verbose

    verbose_output_filename.parent.mkdir(parents=True, exist_ok=True)
    with verbose_output_filename.open("w", encoding="utf-8") as f:
        f.write(verbose_output)

    html_output_filename.parent.mkdir(parents=True, exist_ok=True)
    with html_output_filename.open("w", encoding="utf-8") as f:
        f.write(html_output)

    raise typer.Exit(result)


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()
