<a href="https://www.bigclown.com"><img src="https://s3.eu-central-1.amazonaws.com/bigclown/gh-readme-logo.png" alt="BigClown Logo" align="right"></a>

# Hub Service for BigClown USB Gateway

[![Travis](https://img.shields.io/travis/bigclownlabs/bch-usb-gateway/master.svg)](https://travis-ci.org/bigclownlabs/bch-usb-gateway)
[![Release](https://img.shields.io/github/release/bigclownlabs/bch-usb-gateway.svg)](https://github.com/bigclownlabs/bch-usb-gateway/releases)
[![License](https://img.shields.io/github/license/bigclownlabs/bch-usb-gateway.svg)](https://github.com/bigclownlabs/bch-usb-gateway/blob/master/LICENSE)
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

  ```
  gateway/all/info {"id": "%012llx", "firmware": ""}
  ```

* List of paired nodes
  ```
  mosquitto_pub -t 'gateway/{id}/nodes/get' -n
  ```

  ```
  gateway/{id-gateway}/nodes ["{id-node-0}", "{id-node-id1}", "{id-node-id2}"]
  ```

* Purge all nodes
  ```
  mosquitto_pub -t 'gateway/{id}/nodes/purge' -n
  ```

  ```
  gateway/{id-gateway}/nodes []
  ```

* Add/Pair node
  ```
  mosquitto_pub -t 'gateway/{id}/nodes/add' -m 'aaaa'
  ```

  ```
  gateway/{id}/attach "{id-node}"
  ```

* Remove/Unpair node
  ```
  mosquitto_pub -t 'gateway/{id}/nodes/remove' -m 'aaaa'
  ```

  ```
  gateway/{id}/detach "{id-node}"
  ```

* Scan

  ```
  mosquitto_pub -t 'gateway/{id}/scan/start' -n
  ```

  ```
  mosquitto_pub -t 'gateway/{id}/scan/stop' -n
  ```

  ```
  gateway/{id}/scan "{id-node-0}"
  gateway/{id}/scan "{id-node-1}"
  gateway/{id}/scan "{id-node-2}"
  ...
  ```

* Enrollment mode

  ```
  mosquitto_pub -t 'gateway/{id}/enrollment/start' -n
  ```
  LED start blink
  ```
  gateway/{id}/attach "{id-node-0}"
  gateway/{id}/attach "{id-node-1}"
  ...
  ```

  ```
  mosquitto_pub -t 'gateway/{id}/enrollment/stop' -n
  ```
  LED turns off


* Automatic pairing of all visible nodes

  ```
  mosquitto_pub -t 'gateway/{id}/automatic-pairing/start' -n
  ```
  LED start blink
  ```
  gateway/{id}/attach "{id-node-0}"
  gateway/{id}/attach "{id-node-1}"
  ...
  ```

  ```
  mosquitto_pub -t 'gateway/{id}/automatic-pairing/stop' -n
  ```
  LED turns off

## Node-Red buttons

If you use Node-Red, you can import text below to create buttons in your flow. You can list, pair and delete nodes with a click of the mouse.

```
[{"id":"3bb38e8.d76af72","type":"mqtt in","z":"b1ad2115.7445a","name":"","topic":"#","qos":"2","broker":"ba3b2e25.7c8b7","x":190,"y":260,"wires":[["4a1ce85.3017d18"]]},{"id":"4a1ce85.3017d18","type":"debug","z":"b1ad2115.7445a","name":"","active":true,"console":"false","complete":"false","x":370,"y":260,"wires":[]},{"id":"4ca43c81.0071a4","type":"inject","z":"b1ad2115.7445a","name":"All gateway info","topic":"gateway/all/info/get","payload":"","payloadType":"str","repeat":"","crontab":"","once":false,"x":219,"y":352,"wires":[["a6c1e618.3996d8"]]},{"id":"a6c1e618.3996d8","type":"mqtt out","z":"b1ad2115.7445a","name":"","topic":"","qos":"","retain":"","broker":"ba3b2e25.7c8b7","x":404,"y":353,"wires":[]},{"id":"28b390cb.9d42d","type":"inject","z":"b1ad2115.7445a","name":"Enrollment start","topic":"gateway/192.168.1.100/enrollment/start","payload":"","payloadType":"str","repeat":"","crontab":"","once":false,"x":220,"y":480,"wires":[["b48b000f.19c45"]]},{"id":"b48b000f.19c45","type":"mqtt out","z":"b1ad2115.7445a","name":"","topic":"","qos":"","retain":"","broker":"ba3b2e25.7c8b7","x":405,"y":481,"wires":[]},{"id":"ab7eabbc.aa0988","type":"inject","z":"b1ad2115.7445a","name":"Enrollment stop","topic":"gateway/192.168.1.100/enrollment/stop","payload":"","payloadType":"str","repeat":"","crontab":"","once":false,"x":220,"y":520,"wires":[["a7ab52a6.97a14"]]},{"id":"a7ab52a6.97a14","type":"mqtt out","z":"b1ad2115.7445a","name":"","topic":"","qos":"","retain":"","broker":"ba3b2e25.7c8b7","x":405,"y":521,"wires":[]},{"id":"ca19077c.ed3be8","type":"inject","z":"b1ad2115.7445a","name":"List of paired nodes","topic":"gateway/192.168.1.100/nodes/get","payload":"","payloadType":"str","repeat":"","crontab":"","once":false,"x":230,"y":400,"wires":[["d6c723e6.a72de"]]},{"id":"d6c723e6.a72de","type":"mqtt out","z":"b1ad2115.7445a","name":"","topic":"","qos":"","retain":"","broker":"ba3b2e25.7c8b7","x":405,"y":401,"wires":[]},{"id":"8019bb1c.a76098","type":"inject","z":"b1ad2115.7445a","name":"purge all nodes","topic":"gateway/192.168.1.100/nodes/purge","payload":"","payloadType":"str","repeat":"","crontab":"","once":false,"x":220,"y":700,"wires":[["3ea8f41.1f66f0c"]]},{"id":"3ea8f41.1f66f0c","type":"mqtt out","z":"b1ad2115.7445a","name":"","topic":"","qos":"","retain":"","broker":"ba3b2e25.7c8b7","x":405,"y":701,"wires":[]},{"id":"86686e4a.8480b","type":"inject","z":"b1ad2115.7445a","name":"auto pair start","topic":"gateway/192.168.1.100/automatic-pairing/start","payload":"","payloadType":"str","repeat":"","crontab":"","once":false,"x":210,"y":580,"wires":[["8fb42dcb.6d776"]]},{"id":"8fb42dcb.6d776","type":"mqtt out","z":"b1ad2115.7445a","name":"","topic":"","qos":"","retain":"","broker":"ba3b2e25.7c8b7","x":405,"y":581,"wires":[]},{"id":"5962b3a1.307a6c","type":"inject","z":"b1ad2115.7445a","name":"auto pair stop","topic":"gateway/192.168.1.100/automatic-pairing/stop","payload":"","payloadType":"str","repeat":"","crontab":"","once":false,"x":210,"y":620,"wires":[["63b0aab2.6b8444"]]},{"id":"63b0aab2.6b8444","type":"mqtt out","z":"b1ad2115.7445a","name":"","topic":"","qos":"","retain":"","broker":"ba3b2e25.7c8b7","x":405,"y":621,"wires":[]},{"id":"ba3b2e25.7c8b7","type":"mqtt-broker","z":"","broker":"localhost","port":"1883","clientid":"","usetls":false,"compatmode":true,"keepalive":"60","cleansession":true,"willTopic":"","willQos":"0","willPayload":"","birthTopic":"","birthQos":"0","birthPayload":""}]
```

## Serial talk

Send:
["$/info/get", null]

Response:
["$/info", {"id": "%012llx", "firmware": ""}]


## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT/) - see the [LICENSE](LICENSE) file for details.

---

Made with &#x2764;&nbsp; by [BigClown Labs s.r.o.](https://www.bigclown.com) in Czech Republic.
