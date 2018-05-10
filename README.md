# bnbLockClient

An mqtt connector for ZWave devices that broadcasts its endpoints to a web application for dynamic and painless device programming.

There are only a few implemented control and display types

The implemented control types include:
* Binary Switch
* Numerical input
    * Password input

And the implemented display types include:
* Binary Switch
* Text display

Each control type is communicated to the bnbHome website so that it becomes possible to effortlessly add more device types just from the client by adding as many generic control and display types as needed.

An endpoint may look like:

`.../lockid/set/lockstate`\
`.../lockid/get/lockstate`