.PHONY: all
all:
	sudo apt update \
	&& sudo apt install python3-pip \
	&& sudo apt install python3-venv \
	&& sudo apt install git \
	&& git clone https://github.com/NelsonIg/OPC-UA.git \
	&& python3 -m venv ./venv \
	&& source ./venv/bin/activate \
	&& pip3 install -r requirements.txt \
	&& sudo apt install python3-numpy \
	&& sudo apt install python3-pandas
