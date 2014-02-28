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

R ?= $(shell lsb_release -cs)

DEB_VERSION = $(shell head -1 changelog | awk '{print $$2}' | tr -d '()')

SRC_VERSION = $(shell echo $(DEB_VERSION) | awk -F- '{print $$1}')
SRC_NAME = dwarf-$(SRC_VERSION)

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

orig: clean
	rm -rf build || true
	mkdir -p build/$(SRC_NAME)
	tar -cvf - bin dwarf etc setup.py README | \
		tar -C build/$(SRC_NAME) -xf -
	cd build && tar -czvf dwarf_$(SRC_VERSION).orig.tar.gz $(SRC_NAME)

distro: orig
	tar -cvf - debian | tar -C build/$(SRC_NAME) -xf -
	sed -s 's/RELEASE/$(R)/' changelog > build/$(SRC_NAME)/debian/changelog

deb: distro
	cd build/$(SRC_NAME) && debuild -uc -us

src: distro
	cd build/$(SRC_NAME) && debuild -S -sa

ppa: src
	cd build && dput ppa:juergh/dwarf dwarf_$(DEB_VERSION)_source.changes

clean:
	@find . \( -name .tox -o -name .git \) -prune -o \
		\( -name '*~' -o -name '*.pyc' \) -type f -print | \
		xargs rm -f
	@rm -r dwarf.egg-info 2>/dev/null || :

deepclean: clean
	@rm -rf build .tox 2>/dev/null || :
	./debian/rules clean

.PHONY: build changelog
