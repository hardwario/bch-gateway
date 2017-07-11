# How install on turris

1. Update
    ```
    opkg update
    ```

2. Install driver
    ```
    opkg install kmod-usb-acm kmod-usb-serial-ftdi
    ```

## From PIP3 or PIP

3. Install Python and pip
    python 3.x
    ```
    opkg install python3 python3-pip
    ```

    or python 2.x
    ```
    opkg install python python-pip
    ```

4. Install bc-gateway   

    python 3.x
    ```
    pip3 install bc-gateway
    ```

    or python 2.x
    ```
    pip install bc-gateway
    ```

5. Test 
    ```
    bc-gateway --help
    ```

6. Run as service

    6.1. Config
    ```
    wget "https://raw.githubusercontent.com/bigclownlabs/bch-usb-gateway/master/turris/bc-gateway.conf" -O /etc/config/bc-gateway
    ```
    
    6.2. Init
    ```
    wget "https://raw.githubusercontent.com/bigclownlabs/bch-usb-gateway/master/turris/bc-gateway.init" -O /etc/init.d/bc-gateway
    ```

    6.3. Enable service
    ```
    /etc/init.d/bc-gateway enable
    ```

    6.4. Start service
    ```
    /etc/init.d/bc-gateway start
    ```

7. Connect usb gateway and check mqtt 

    ```
    mosquitto_sub -v -t '#'
    ```