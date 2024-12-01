cleanup:
	chmod +x cleanup.sh
	./cleanup.sh

set_dev_env:
	rm -f .git/hooks/* .git/hooks/.[!.]* .git/hooks/..?*
	cp cleanup.sh .git/hooks/pre-commit

test:
	cd search/ && python3 -m unittest test_api

start:
	chmod +x start.sh
	./start.sh