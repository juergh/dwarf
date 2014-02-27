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

VERSION = $(shell head -1 ./debian/changelog | awk '{print $$2}' | tr -d '()')

all: tox

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

build:
	rm -rf build/* || true
	mkdir -p build/dwarf-$(VERSION)
	tar cvf - bin debian dwarf etc setup.py README | \
		(cd build/dwarf-$(VERSION) && tar xfp -)

deb: build
	cd build/dwarf-$(VERSION) && debuild -i -us -uc

clean:
	@find . \( -name .tox -o -name .git \) -prune -o \
		\( -name '*~' -o -name '*.pyc' \) -type f -print | \
		xargs rm -f
	@rm -r dwarf.egg-info 2>/dev/null || :

deepclean: clean
	@rm -rf build .tox 2>/dev/null || :

.PHONY: build
