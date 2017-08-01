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

pep8 pylint tests coverage:
	tox -e $@

clean:
	@find . \( -name .tox -o -name .git \) -prune -o \
		\( -name '*~' -o -name '*.pyc' \) -type f -print | \
		xargs rm -f
	@rm -r dwarf.egg-info 2>/dev/null || :
	@rm -f .coverage

deepclean: clean
	@rm -rf .tox 2>/dev/null || :

tgz: VERSION = $(shell git tag | sort -n | tail -1 | tr -d 'v')
tgz:
	git archive --format=tar --prefix=dwarf-$(VERSION)/ master | \
		gzip -9 > ../dwarf-$(VERSION).tar.gz

run:
	sudo su -s /bin/sh -c './bin/dwarf -s' dwarf

init:
	pid=$$(ps -ef | grep './bin/dwarf' | grep sudo | grep -v grep | \
	       awk '{ print $$2 }') ; \
	    if [ "$${pid}" != "" ] ; then \
	        sudo kill $${pid} && \
	        sleep 5 ; \
	    fi
	sudo su -s /bin/sh -c './bin/dwarf-manage db-delete' dwarf
	sudo su -s /bin/sh -c './bin/dwarf-manage db-init' dwarf

release:
	[ -n "$${v}" ] || ( echo "Usage: make release v=<VERSION>" ; false )
	# Update ChangeLog
	( \
	    echo $${v} ; \
	    prev=$$(cat ChangeLog | head -1) ; \
	    git --no-pager log --no-merges --format='  * %s' $${prev}..  ; \
	    echo ; \
	    cat ChangeLog ; \
	) > ChangeLog.new
	mv ChangeLog.new ChangeLog
	# Update debian/changelog.in
	debian/bin/update-changelog.in $${v#v}
	# Update snap/snapcraft.yaml
	sed -i -e "s/^version: .*$$/version: '$${v#v}'/" snap/snapcraft.yaml
	# commit and tag
	git add ChangeLog debian/changelog.in snap/snapcraft.yaml
	git commit -s -m "$${v}"
	git tag -s -m "$${v}" $${v}

debian: BUILDD := $(shell mktemp -d build-XXXXXXXX)
debian:
	git archive --format=tar HEAD | ( cd $(BUILDD) ; tar -xf - )
	cd $(BUILDD) && \
	    ./debian/bin/create-changelog && \
	    dpkg-buildpackage && \
	    rm -rf $(BUILDD)

.PHONY: tox pep8 pylint tests coverage deepclean tgz run init release debian
