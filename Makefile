VERSION = 0.1.0

all: tox

tox:
	tox

pep8:
	tox -e pep8

pylint:
	tox -e pylint

build:
	rm -rf build/* || true
	mkdir -p build/dwarf-$(VERSION)
	tar cvf - bin debian dwarf etc setup.py | \
		(cd build/dwarf-$(VERSION) && tar xfp -)

deb: build
	cd build/dwarf-$(VERSION) && debuild -i -us -uc

clean:
	@find . \( -name .tox -o -name .git \) -prune -o \
		\( -name '*~' -o -name '*.pyc' \) -type f -print | \
		xargs rm -f
	@rm -r dwarf.egg-info 2>/dev/null || :

deepclean: clean
	@rm -rf build 2>/dev/null || :

.PHONY: build
