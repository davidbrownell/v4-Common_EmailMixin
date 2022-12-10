# ----------------------------------------------------------------------
# |
# |  SmtpMailer.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2022-12-09 15:28:03
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2022
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the SmtpMailer object"""

import json
import mimetypes
import smtplib
import ssl
import textwrap

from dataclasses import dataclass, field
from email import encoders
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from pathlib import Path
from typing import Generator, List, Optional

from Common_Foundation.ContextlibEx import ExitStack
from Common_Foundation.Shell.All import CurrentShell


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class SmtpMailer(object):
    """Code that manages SMTP profiles and uses them to send messages"""

    # ----------------------------------------------------------------------
    # |  Public Types
    PROFILE_EXTENSION                       = ".SmtpMailer"

    # ----------------------------------------------------------------------
    # |  Public Data
    host: str
    username: str
    password: str
    from_name: str
    from_email: str

    ssl: bool                               = field(kw_only=True)

    port: Optional[int]                     = field(default=None)

    # ----------------------------------------------------------------------
    # |  Public Methods
    def ToString(
        self,
        *,
        show_password: bool=False,
    ) -> str:
        return textwrap.dedent(
            """\
            host        : {host}
            username    : {username}
            password    : {password}
            from_name   : {from_name}
            from_email  : {from_email}
            ssl         : {ssl}
            port        : {port}
            """,
        ).format(
            host=self.host,
            username=self.username,
            password=self.password if show_password else "****",
            from_name=self.from_name,
            from_email=self.from_email,
            ssl=self.ssl,
            port=self.port,
        )

    # ----------------------------------------------------------------------
    def Save(
        self,
        profile_name: str,
    ) -> None:
        """Saves a profile"""

        content = json.dumps(self.__dict__)

        if CurrentShell.family_name == "Windows":
            import win32crypt

            content = win32crypt.CryptProtectData(content.encode("utf-8"), "", None, None, None, 0)

        with (CurrentShell.user_directory / (profile_name + self.__class__.PROFILE_EXTENSION)).open("wb") as f:
            f.write(content)

    # ----------------------------------------------------------------------
    def SendMessage(
        self,
        recipients: List[str],
        subject: str,
        message: str,
        attachment_filenames: Optional[List[Path]]=None,
        message_format: str="plain", # "html"
    ) -> None:
        """Sends an email message using the current profile"""

        if self.ssl:
            port = self.port or 465
            smtp = smtplib.SMTP_SSL(self.host, port, context=ssl.create_default_context())
        else:
            port = self.port or 26
            smtp = smtplib.SMTP(self.host, port)

        smtp.connect(self.host, port)
        with ExitStack(smtp.close):
            if not self.ssl:
                smtp.starttls()

            smtp.login(self.username, self.password)

            from_addr = "{} <{}>".format(self.from_name, self.from_email)

            if not attachment_filenames:
                msg = MIMEMultipart("alternative")
            else:
                msg = MIMEMultipart()

            msg["Subject"] = subject
            msg["From"] = from_addr
            msg["To"] = ", ".join(recipients)

            msg.attach(MIMEText(message, message_format))

            for attachment_filename in (attachment_filenames or []):
                ctype, encoding = mimetypes.guess_type(attachment_filename)

                if ctype is None or encoding is not None:
                    ctype = "application/octet-stream"

                maintype, subtype = ctype.split("/", 1)

                with attachment_filename.open("rb") as f:
                    content = f.read()

                if maintype == "text":
                    attachment = MIMEText(content.decode("utf-8"), _subtype=subtype)
                elif maintype == "image":
                    attachment = MIMEImage(content, _subtype=subtype)
                elif maintype == "audio":
                    attachment = MIMEAudio(content, _subtype=subtype)
                else:
                    attachment = MIMEBase(maintype, subtype)

                    attachment.set_payload(content)
                    encoders.encode_base64(attachment)

                attachment.add_header("Content-Disposition", "attachment", filename=attachment_filename.name)

                msg.attach(attachment)

            smtp.sendmail(from_addr, recipients, msg.as_string())

    # ----------------------------------------------------------------------
    @classmethod
    def Load(
        cls,
        profile_name: str,
    ) -> "SmtpMailer":
        """Loads a previously saved file"""

        data_filename = CurrentShell.user_directory / (profile_name + cls.PROFILE_EXTENSION)

        if not data_filename.is_file():
            raise Exception("'{}' is not a recognized profile name.".format(profile_name))

        with data_filename.open("rb") as f:
            content = f.read()

        if CurrentShell.family_name == "Windows":
            import win32crypt

            content = win32crypt.CryptUnprotectData(content, None, None, None, 0)
            content = content[1].decode("utf-8")

        return cls(**json.loads(content))

    # ----------------------------------------------------------------------
    @classmethod
    def EnumProfiles(cls) -> Generator[str, None, None]:
        for item in CurrentShell.user_directory.iterdir():
            if item.suffix == cls.PROFILE_EXTENSION:
                yield item.stem
