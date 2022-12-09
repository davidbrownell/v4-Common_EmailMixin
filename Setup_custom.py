# ----------------------------------------------------------------------
# |
# |  Setup_custom.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2022-12-09 15:01:50
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2022
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
# pylint: disable=missing-module-docstring

import uuid                                             # pylint: disable=unused-import

from typing import Dict, List, Optional, Union

from semantic_version import Version as SemVer          # pylint: disable=unused-import

from Common_Foundation.Shell.All import CurrentShell                        # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation.Shell import Commands                                # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation.Streams.DoneManager import DoneManager               # type: ignore  # pylint: disable=import-error,unused-import

from RepositoryBootstrap import Configuration                               # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap import Constants                                   # type: ignore  # pylint: disable=import-error,unused-import


# ----------------------------------------------------------------------
@Configuration.MixinRepository
def GetConfigurations() -> Union[
    Configuration.Configuration,
    Dict[
        str,                                # configuration name
        Configuration.Configuration,
    ],
]:
    return Configuration.Configuration(
        "",
        [
            Configuration.Dependency(
                Constants.COMMON_FOUNDATION_REPOSITORY_ID,
                "Common_Foundation",
                "python310",
                "https://github.com/davidbrownell/v4-Common_Foundation.git",
            ),
        ],
        Configuration.VersionSpecs(
            [],                             # tools
            {},                             # libraries
        ),
    )


# ----------------------------------------------------------------------
# Note that it is safe to remove this function if it will never be used.
def GetCustomActions(
    # Note that it is safe to remove any parameters that are not used
    dm: DoneManager,                                    # pylint: disable=unused-argument
    explicit_configurations: Optional[List[str]],       # pylint: disable=unused-argument
    force: bool,                                        # pylint: disable=unused-argument
    interactive: Optional[bool],                        # pylint: disable=unused-argument
) -> List[Commands.Command]:
    """Return custom actions invoked as part of the setup process for this repository"""

    return []
