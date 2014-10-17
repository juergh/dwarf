# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013 OpenStack Foundation
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

tox:
	tox

pep8:
	tox -e pep8

pylint:
	tox -e pylint

test:
	tox -e py27

cover:
	tox -e cover

clean:
	@find . \( -name .tox -o -name .git \) -prune -o \
		\( -name '*~' -o -name '*.pyc' \) -type f -print | \
		xargs rm -f
	@rm -r dwarf.egg-info 2>/dev/null || :

deepclean: clean
	@rm -rf .tox 2>/dev/null || :

tgz: VERSION = $(shell git tag | sort -n | tail -1 | tr -d 'v')
tgz:
	git archive --format=tar --prefix=dwarf-$(VERSION)/ master | \
		gzip -9 > ../dwarf-$(VERSION).tar.gz

run:
	sudo su -s /bin/sh -c './bin/dwarf' dwarf
