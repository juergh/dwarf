#!/usr/bin/env python
#
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dwarf import config


config._BASE_CONFIG = {   # pylint: disable=W0212
    'instances_dir': '/tmp/dwarf/instances',
    'instances_base_dir': '/tmp/dwarf/instances/_base',
    'images_dir': '/tmp/dwarf/images',
    'dwarf_db': '/tmp/dwarf/dwarf.db',
    'dwarf_log': '/tmp/dwarf/dwarf.log',
}
