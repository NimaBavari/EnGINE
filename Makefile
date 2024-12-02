cleanup:
	chmod +x cleanup.sh
	./cleanup.sh

set_dev_env:
	chmod +x set_pre_commit.sh
	./set_pre_commit.sh

test:
	chmod +x test.sh
	./test.sh

start:
	chmod +x start.sh
	./start.sh