<a href="https://www.bigclown.com/"><img src="https://bigclown.sirv.com/logo.png" width="200" height="59" alt="BigClown Logo" align="right"></a>

# Hub Service for BigClown USB Gateway

[![Travis](https://img.shields.io/travis/bigclownlabs/bch-gateway/master.svg)](https://travis-ci.org/bigclownlabs/bch-gateway)
[![Release](https://img.shields.io/github/release/bigclownlabs/bch-gateway.svg)](https://github.com/bigclownlabs/bch-gateway/releases)
[![License](https://img.shields.io/github/license/bigclownlabs/bch-gateway.svg)](https://github.com/bigclownlabs/bch-gateway/blob/master/LICENSE)
[![Twitter](https://img.shields.io/twitter/follow/BigClownLabs.svg?style=social&label=Follow)](https://twitter.com/BigClownLabs)

This repository contains CLI service for BigClown USB Gateway.

## Introduction

The service connects to a serial port where BigClown USB Gateway is connected.
It converts messages from serial port to MQTT broker and vice versa.
Run with `--help` parameter to see the available options.
It works with Python 2.7+ and Python 3.5+ environments and it has been tested under Linux, macOS and Windows.


## MQTT

* Get info about all connected gateway
  ```
  mosquitto_pub -t 'gateway/all/info/get' -n
  ```

    response:
    ```
    gateway/{name}/info {"id": "836d19839c3b", "firmware": "bcf-gateway-...."}
    ```

* List of paired nodes
  ```
  mosquitto_pub -t 'gateway/{name}/nodes/get' -n
  ```

    response:
    ```
    gateway/{name}/nodes ["{id-node-0}", "{id-node-id1}", "{id-node-id2}"]
    ```

* Pairing mode

  * Start
    ```
    mosquitto_pub -t 'gateway/{name}/pairing-mode/start' -n
    ```
      LED on gateway start blink

      response:
      ```
      gateway/{name}/pairing-mode "start"
      ```

      Gateway is waiting to pair node. To pare node, long press the button on Core Module.

      response when the node is successfully added:
      ```
      gateway/{name}/attach "{id-node-0}"
      gateway/{name}/attach "{id-node-1}"
      ...
      ```

      Error response if there is not enough space:
      ```
      gateway/{name}/attach-failure "{id-node-1}"
      ```

  * Stop
    ```
    mosquitto_pub -t 'gateway/{name}/pairing-mode/stop' -n
    ```
      LED on gateway turns off

      response:
      ```
      gateway/{name}/pairing-mode "stop"
      ```

* Purge all nodes
  ```
  mosquitto_pub -t 'gateway/{name}/nodes/purge' -n
  ```

    response:
    ```
    gateway/{name}/nodes []
    ```

* Manual Add/Pair node
  ```
  mosquitto_pub -t 'gateway/{name}/nodes/add' -m '"{id-node}"'
  ```

    response:
    ```
    gateway/{name}/attach "{id-node}"
    ```

    Error response if there is not enough space:
    ```
    gateway/{name}/attach-failure "{id-node-1}"
    ```

* Manual Remove/Unpair node
  ```
  mosquitto_pub -t 'gateway/{name}/nodes/remove' -m '"{id-node}"'
  ```

    response:
    ```
    gateway/{name}/detach "{id-node}"
    ```

* Set node alias
  ```
  mosquitto_pub -t 'gateway/usb-dongle/alias/set' -m '{"id": "id-node", "alias": "new-alias"}'
  ```

    respose:
    ```
    gateway/usb-dongle/alias/set/ok {"id": "id-node", "alias": "new-alias"}
    ```


* Remove node alias
  ```
  mosquitto_pub -t 'gateway/usb-dongle/alias/remove' -m '"{id-node}"'
  ```
  ```
  mosquitto_pub -t 'gateway/usb-dongle/alias/set' -m '{"id": "id-node", "alias": null}'
  ```

* Scan Start

  * Start
    ```
    mosquitto_pub -t 'gateway/{name}/scan/start' -n
    ```

      response:
      ```
      gateway/{name}/scan "start"
      ```

      response for unknown node
      ```
      gateway/{name}/found "{id-node-0}"
      gateway/{name}/found "{id-node-1}"
      gateway/{name}/found "{id-node-2}"
      ...
      ```

  * Stop
    ```
    mosquitto_pub -t 'gateway/{name}/scan/stop' -n
    ```

      response:
      ```
      gateway/{name}/scan "stop"
      ```

* Automatic pairing of all visible nodes

  !!! This is experimental features do not all work

  * Start

    ```
    mosquitto_pub -t 'gateway/{name}/automatic-pairing/start' -n
    ```

      LED on gateway start blink

      response:
      ```
      gateway/{name}/automatic-pairing "start"
      ```

      response when the node is successfully added:
      ```
      gateway/{name}/attach "{id-node-0}"
      gateway/{name}/attach "{id-node-1}"
      ...
      ```

  * Stop
      ```
      mosquitto_pub -t 'gateway/{name}/automatic-pairing/stop' -n
      ```

        LED on gateway turns off

        response:
        ```
        gateway/{name}/automatic-pairing "stop"
        ```

## Configuration file

* name: string

  support variables:
  * {ip} - ip address
  * {id} - the id of the connected usb-dongle or core-module

  default: null - automatic detect name from gateway firmware

  example: "{ip}-ttyUSB0"

## Node-Red buttons

If you use Node-Red, you can import text below to create buttons in your flow. You can list, pair and delete nodes with a click of the mouse.

* For bcf-gateway-usb-dongle

  ```
  [{"id":"83c6c60c.209d78","type":"mqtt in","z":"97027127.a55f7","name":"","topic":"#","qos":"2","broker":"de273190.7f6f2","x":610,"y":80,"wires":[["454a64bc.50f77c"]]},{"id":"454a64bc.50f77c","type":"debug","z":"97027127.a55f7","name":"","active":true,"console":"false","complete":"false","x":790,"y":80,"wires":[]},{"id":"9e87ab30.a50be8","type":"inject","z":"97027127.a55f7","name":"All gateway info","topic":"gateway/all/info/get","payload":"","payloadType":"str","repeat":"","crontab":"","once":false,"x":639,"y":172,"wires":[["504dd396.bb5b4c"]]},{"id":"504dd396.bb5b4c","type":"mqtt out","z":"97027127.a55f7","name":"","topic":"","qos":"","retain":"","broker":"de273190.7f6f2","x":824,"y":173,"wires":[]},{"id":"f447966d.ed0cb8","type":"inject","z":"97027127.a55f7","name":"Pairing mode start","topic":"gateway/usb-dongle/pairing-mode/start","payload":"","payloadType":"str","repeat":"","crontab":"","once":false,"x":660,"y":280,"wires":[["ae043e16.df77c"]]},{"id":"ae043e16.df77c","type":"mqtt out","z":"97027127.a55f7","name":"","topic":"","qos":"","retain":"","broker":"de273190.7f6f2","x":825,"y":281,"wires":[]},{"id":"80092576.c83998","type":"inject","z":"97027127.a55f7","name":"Pairing mode stop","topic":"gateway/usb-dongle/pairing-mode/stop","payload":"","payloadType":"str","repeat":"","crontab":"","once":false,"x":660,"y":320,"wires":[["86c93689.7d0e58"]]},{"id":"86c93689.7d0e58","type":"mqtt out","z":"97027127.a55f7","name":"","topic":"","qos":"","retain":"","broker":"de273190.7f6f2","x":825,"y":321,"wires":[]},{"id":"8f7b14c7.898c38","type":"inject","z":"97027127.a55f7","name":"List of paired nodes","topic":"gateway/usb-dongle/nodes/get","payload":"","payloadType":"str","repeat":"","crontab":"","once":false,"x":650,"y":220,"wires":[["75f5e8db.ed19a8"]]},{"id":"75f5e8db.ed19a8","type":"mqtt out","z":"97027127.a55f7","name":"","topic":"","qos":"","retain":"","broker":"de273190.7f6f2","x":825,"y":221,"wires":[]},{"id":"ed3cfe08.3321b","type":"inject","z":"97027127.a55f7","name":"purge all nodes","topic":"gateway/usb-dongle/nodes/purge","payload":"","payloadType":"str","repeat":"","crontab":"","once":false,"x":640,"y":380,"wires":[["2acde0de.0d9de"]]},{"id":"2acde0de.0d9de","type":"mqtt out","z":"97027127.a55f7","name":"","topic":"","qos":"","retain":"","broker":"de273190.7f6f2","x":825,"y":381,"wires":[]},{"id":"de273190.7f6f2","type":"mqtt-broker","z":"","broker":"localhost","port":"1883","clientid":"","usetls":false,"compatmode":true,"keepalive":"60","cleansession":true,"willTopic":"","willQos":"0","willPayload":"","birthTopic":"","birthQos":"0","birthPayload":""}]
  ```

* For bcf-gateway-core-module
  ```
  [{"id":"47ab49a8.0a88f8","type":"mqtt in","z":"97027127.a55f7","name":"","topic":"#","qos":"2","broker":"deefb40d.51f818","x":370,"y":100,"wires":[["7208a9c6.a8d3e8"]]},{"id":"7208a9c6.a8d3e8","type":"debug","z":"97027127.a55f7","name":"","active":true,"console":"false","complete":"false","x":550,"y":100,"wires":[]},{"id":"3e634a0c.8e15e6","type":"inject","z":"97027127.a55f7","name":"All gateway info","topic":"gateway/all/info/get","payload":"","payloadType":"str","repeat":"","crontab":"","once":false,"x":399,"y":192,"wires":[["84e9ef97.a81d5"]]},{"id":"84e9ef97.a81d5","type":"mqtt out","z":"97027127.a55f7","name":"","topic":"","qos":"","retain":"","broker":"deefb40d.51f818","x":584,"y":193,"wires":[]},{"id":"6d1a6395.7b49ac","type":"inject","z":"97027127.a55f7","name":"Pairing mode start","topic":"gateway/core-module/pairing-mode/start","payload":"","payloadType":"str","repeat":"","crontab":"","once":false,"x":400,"y":320,"wires":[["6bb142ef.da565c"]]},{"id":"6bb142ef.da565c","type":"mqtt out","z":"97027127.a55f7","name":"","topic":"","qos":"","retain":"","broker":"deefb40d.51f818","x":585,"y":321,"wires":[]},{"id":"191cf80e.901568","type":"inject","z":"97027127.a55f7","name":"Pairing mode stop","topic":"gateway/core-module/pairing-mode/stop","payload":"","payloadType":"str","repeat":"","crontab":"","once":false,"x":400,"y":360,"wires":[["11669b55.138775"]]},{"id":"11669b55.138775","type":"mqtt out","z":"97027127.a55f7","name":"","topic":"","qos":"","retain":"","broker":"deefb40d.51f818","x":585,"y":361,"wires":[]},{"id":"de1bca38.1214f8","type":"inject","z":"97027127.a55f7","name":"List of paired nodes","topic":"gateway/core-module/nodes/get","payload":"","payloadType":"str","repeat":"","crontab":"","once":false,"x":410,"y":240,"wires":[["7cb77d25.465514"]]},{"id":"7cb77d25.465514","type":"mqtt out","z":"97027127.a55f7","name":"","topic":"","qos":"","retain":"","broker":"deefb40d.51f818","x":585,"y":241,"wires":[]},{"id":"ec929b66.dddbb8","type":"inject","z":"97027127.a55f7","name":"purge all nodes","topic":"gateway/core-module/nodes/purge","payload":"","payloadType":"str","repeat":"","crontab":"","once":false,"x":400,"y":420,"wires":[["afe70282.f5ead"]]},{"id":"afe70282.f5ead","type":"mqtt out","z":"97027127.a55f7","name":"","topic":"","qos":"","retain":"","broker":"deefb40d.51f818","x":585,"y":421,"wires":[]},{"id":"deefb40d.51f818","type":"mqtt-broker","z":"","broker":"localhost","port":"1883","clientid":"","usetls":false,"compatmode":true,"keepalive":"60","cleansession":true,"willTopic":"","willQos":"0","willPayload":"","birthTopic":"","birthQos":"0","birthPayload":""}]
  ```

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT/) - see the [LICENSE](LICENSE) file for details.

---

Made with &#x2764;&nbsp; by [**HARDWARIO s.r.o.**](https://www.hardwario.com/) in the heart of Europe.
