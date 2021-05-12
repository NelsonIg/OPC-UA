.PHONY: all
all:
	sudo apt install python3-pip \
	&& pip3 install -r requirements.txt \
	&& sudo apt install python3-numpy \
	&& sudo apt install python3-pandas

.PHONY: raspi-server-test
raspi-server-test:
	python3 server/server_example.py localhost 
