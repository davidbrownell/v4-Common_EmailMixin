# ----------------------------------------------------------------------
# |
# |  __main__.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-03-14 07:57:39
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Sends an email message that includes the result on logs of an executed process."""

import sys

from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Optional

import typer

from typer.core import TyperGroup

from Common_Foundation.ContextlibEx import ExitStack
from Common_Foundation import PathEx
from Common_Foundation.Shell.All import CurrentShell
from Common_Foundation.Streams.Capabilities import Capabilities
from Common_Foundation.Streams.DoneManager import DoneManager, DoneManagerFlags
from Common_Foundation.Streams.StreamDecorator import StreamDecorator
from Common_Foundation import SubprocessEx

from Common_EmailMixin.SmtpMailer import SmtpMailer


# ----------------------------------------------------------------------
sys.path.insert(0, str(PathEx.EnsureDir(Path(__file__).parent / "Impl")))
with ExitStack(lambda: sys.path.pop(0)):
    from Impl.ansi2html.converter import Ansi2HTMLConverter


# ----------------------------------------------------------------------
class NaturalOrderGrouper(TyperGroup):
    # pylint: disable=missing-class-docstring
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
@app.command(
    "EntryPoint",
    help=__doc__,
    no_args_is_help=True,
)
def EntryPoint(
    command_line: str=typer.Argument(..., help="Command line to invoke; all output will be included in the email message."),
    smtp_profile_name: str=typer.Argument(..., help="SMTP profile name; use 'CreateSmtpMailer{}' to list existing profiles or create a new profile.".format(CurrentShell.script_extensions[0])),
    email_recipients: list[str]=typer.Argument(..., help="Recipient(s) for the email message."),
    email_subject: str=typer.Argument(..., help="Subject of the email message; '{now}' can be used in the string as a template placeholder for the current time."),
    command_line_desc: Optional[str]=typer.Option(None, "--command-line-desc", help="Description of the command line used within the email message; provide this value if the command line contains passwords or other sensitive information."),
    background_color: str=typer.Option("black", "--background-color", help="Email background color."),
    verbose: bool=typer.Option(False, "--verbose", help="Write verbose information to the terminal."),
    debug: bool=typer.Option(False, "--debug", help="Write debug information to the terminal."),
) -> None:
    with DoneManager.CreateCommandLine(
        output_flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        if command_line_desc is None:
            command_line_desc = command_line

        try:
            smtp_mailer = SmtpMailer.Load(smtp_profile_name)
        except Exception as ex:
            dm.WriteError(str(ex))
            return

        with dm.Nested(
            "Running '{}'...".format(command_line_desc),
            suffix="\n",
        ) as running_dm:
            # Create the stream used to capture the message content
            message_sink = StringIO()

            Capabilities.Create(
                message_sink,
                #columns=120,
                is_interactive=False,
                supports_colors=True,
                is_headless=True,
                no_column_warning=True,
            )

            with running_dm.YieldStream() as dm_stream:
                running_dm.result = SubprocessEx.Stream(
                    command_line,
                    StreamDecorator([message_sink, dm_stream]),
                )

            message = message_sink.getvalue()

        # Value to convert spaces into before the text is converted to html.
        space_placeholder = "__nbsp;__"

        with dm.Nested("Converting output to HTML..."):
            message = message.replace(" ", space_placeholder)

            message = Ansi2HTMLConverter(
                dark_bg=True,
                inline=True,
                line_wrap=False,
            ).convert(message)

        for source, dest in [
            (space_placeholder, "&nbsp;"),
            # Create a div to set the background color
            (
                '<pre class="ansi2html-content">\n',
                '<pre class="ansi2html-content">\n<div style="background-color: {}">\n'.format(background_color),
            ),
            # Undo the div that set the background color
            (
                "</pre>\n",
                "</div>\n</pre>\n",
            ),
        ]:
            message = message.replace(source, dest)

        with dm.Nested("Sending email...") as email_dm:
            try:
                smtp_mailer.SendMessage(
                    email_recipients,
                    email_subject.format(now=datetime.now()),
                    message,
                    message_format="html",
                )
            except Exception as ex:
                email_dm.WriteError(str(ex))
                return


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()
