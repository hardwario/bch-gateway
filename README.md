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


## Serial talk

Send:
["$/info/get", null]

Response:
["$/info", {"id": "%012llx", "firmware": ""}]


## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT/) - see the [LICENSE](LICENSE) file for details.

---

Made with &#x2764;&nbsp; by [BigClown Labs s.r.o.](https://www.bigclown.com) in Czech Republic.
