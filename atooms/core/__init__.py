# This file is part of atooms
# Copyright 2010-2014, Daniele Coslovich

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

"""
Global variables.
"""

__author__ = "Daniele Coslovich <daniele.coslovich@umontpellier.fr>"

from ._version import __version__

try:
    from ._commit import __commit__, __date__
except ImportError:
    __commit__ = ""
    __date__ = ""

ndim = 3
"""Number of spatial dimensions."""
