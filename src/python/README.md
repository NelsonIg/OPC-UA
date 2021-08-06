# Raspberry Pi Setup Server
## Image
Download  [Raspberry Pi Imager](https://www.raspberrypi.org/documentation/installation/installing-images/)  
32-Bit Lite Version used here

## Setup Raspberry Pi
+ load empy "ssh" file on SD-Card
+ create 'wpa_supplicant.conf' like below:  
```
country=DE
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
network={
       ssid="Wifi Name"
       psk="Wifi Password"
       key_mgmt=WPA-PSK
}
``` 
## Dependencies for Raspberrypi
```
sudo apt update
sudo apt install git
git clone <link>
cd ./OPC-UA/src
make all
```
## Usefull commands
### Linux  
Show interface configurations
```
ifconfig
```
Shut interface Down/ Up  
```
sudo ifconfig wlan0 up/ down
```
### Microsoft/ Linux  
Show known IPs
```
arp -a
```
