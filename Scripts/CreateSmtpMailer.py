# ----------------------------------------------------------------------
# |
# |  CreateSmtpMailer.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2022-12-09 15:09:43
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2022
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Creates, Lists, and Verifies SmtpMailer profiles"""

import datetime
import getpass
import textwrap

from pathlib import Path
from typing import List, Optional

import typer

from typer.core import TyperGroup

from Common_Foundation.Streams.DoneManager import DoneManager, DoneManagerFlags

from Common_EmailMixin.SmtpMailer import SmtpMailer


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
_profile_name_argument                      = typer.Argument(..., help="Name used to uniquely identify a collection of SMTP settings stored within a profile.")


# ----------------------------------------------------------------------
@app.command("Create", no_args_is_help=True)
def Create(
    profile_name: str=_profile_name_argument,
    host: str=typer.Argument(..., help="SMTP server hostname."),
    username: str=typer.Argument(..., help="SMTP server username."),
    from_name: str=typer.Argument(..., help="Name used when messages are sent."),
    from_email: str=typer.Argument(..., help="Email used when messages are sent."),
    port: Optional[int]=typer.Option(None, min=1, help="SMTP server port."),
    ssl: bool=typer.Option(False, "--ssl", help="Use SSL to connect to the SMTP server."),
    password: Optional[str]=typer.Option(None, help="SMTP server password; you will be prompted for the password if it is not provided on the command line."),
    verbose: bool=typer.Option(False, "--verbose", help="Write verbose information to the terminal."),
    debug: bool=typer.Option(False, "--debug", help="Write debug information to the terminal."),
) -> None:
    """Creates a new SmtpMailer profile."""

    if password is None:
        while not password:
            password = getpass.getpass("Please enter them SMTP server password: ")

    with DoneManager.CreateCommandLine(
        output_flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        with dm.Nested("Creating the profile '{}'...".format(profile_name)):
            SmtpMailer(
                host,
                username,
                password,
                port=port,
                from_name=from_name,
                from_email=from_email,
                ssl=ssl,
            ).Save(profile_name)


# ----------------------------------------------------------------------
@app.command("List", no_args_is_help=False)
def ListFunc(
    verbose: bool=typer.Option(False, "--verbose", help="Write verbose information to the terminal."),
    debug: bool=typer.Option(False, "--debug", help="Write debug information to the terminal."),
) -> None:
    """Lists SmtpMailer profiles."""

    with DoneManager.CreateCommandLine(
        output_flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        dm.WriteLine(
            textwrap.dedent(
                """\

                Available profiles:
                {}

                """,
            ).format(
                "\n".join("    - {}".format(profile) for profile in SmtpMailer.EnumProfiles()),
            ),
        )


# ----------------------------------------------------------------------
@app.command("Display", no_args_is_help=True)
def Display(
    profile_name: str=_profile_name_argument,
    show_password: bool=typer.Option(False, "--show-password", help="Show the password; by default it is masked for security."),
    verbose: bool=typer.Option(False, "--verbose", help="Write verbose information to the terminal."),
    debug: bool=typer.Option(False, "--debug", help="Write debug information to the terminal."),
) -> None:
    """Displays the settings of a profile."""

    with DoneManager.CreateCommandLine(
        output_flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        with dm.Nested(
            "Loading profile...",
            suffix="\n",
        ):
            mailer = SmtpMailer.Load(profile_name)

        dm.WriteLine(mailer.ToString(show_password=show_password))
        dm.WriteLine("")


# ----------------------------------------------------------------------
@app.command("Verify", no_args_is_help=True)
def Verify(
    profile_name: str=_profile_name_argument,
    recipients: List[str]=typer.Argument(..., help="Email recipients (multiple can be provided)."),
    attachments: Optional[List[Path]]=typer.Option(None, "--attachment", resolve_path=True, exists=True, dir_okay=False, help="Optional attachments to include with the message."),
    verbose: bool=typer.Option(False, "--verbose", help="Write verbose information to the terminal."),
    debug: bool=typer.Option(False, "--debug", help="Write debug information to the terminal."),
) -> None:
    """Verifies a SmtpMailer profile by using it to send a test message."""

    with DoneManager.CreateCommandLine(
        output_flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        with dm.Nested(
            "Loading profile...",
            suffix="\n",
        ):
            mailer = SmtpMailer.Load(profile_name)

        mailer.SendMessage(
            recipients,
            "SmtpMailer Verification ({})".format(datetime.datetime.now()),
            "This is a test message to ensure that the profile '{}' is working as expected.\n".format(profile_name),
            attachments,
        )


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()
