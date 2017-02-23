FGPATH=/var/www/FutureGateway
APACHECONFPATH=/etc/apache2/sites-available/
FILES= *.py *.md *.json *.conf *.txt LICENSE
deb:
	mkdir -p ubuntu$(FGPATH)
	mkdir -p ubuntu$(APACHECONFPATH)
	cp -rf $(FILES) ubuntu$(FGPATH)
	cp -rf apache/*.conf ubuntu$(APACHECONFPATH)
	mkdir -p package
	dpkg-deb --build ubuntu package
