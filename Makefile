cleanup:
	chmod +x pre-commit
	./pre-commit

test:
	cd search/ && python3 -m unittest test_api

start:
	chmod +x start.sh
	./start.sh