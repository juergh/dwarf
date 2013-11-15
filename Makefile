all: tox

tox:
	tox

pep8:
	tox -e pep8

pylint:
	tox -e pylint

tgz:
	tar --xform 's,^,dwarf-0.0.1/,' --create --gzip --verbose \
		--file ../dwarf_0.0.1.tar.gz \
		bin debian dwarf etc init

build:
	rm -rf build/* || true
	mkdir -p build/dwarf-0.0.1
	tar cvf - bin debian dwarf etc setup.py | \
		(cd build/dwarf-0.0.1 && tar xfp -)

deb: build
	cd build/dwarf-0.0.1 && debuild -i -us -uc

clean:
	@find . \( -name .tox -o -name .git \) -prune -o \
		\( -name '*~' -o -name '*.pyc' \) -type f -print | \
		xargs rm -f
	@rm -r dwarf.egg-info 2>/dev/null || :

.PHONY: build
