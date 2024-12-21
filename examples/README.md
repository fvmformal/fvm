# Examples

These are some examples that we have done to test the methodology.
Here we order them from easiest to most difficult. We also use the 
friendliness tool from the methodology to check the friendliness score 
of each example, although it may vary depending on the generics.

## Contents

- [``counter``](counter): a simple up counter. Very easy to verify. Friendliness score:
  99.04%.
- [``countervunit``](countervunit): a simple up counter. Very easy to verify. 
  Friendliness score: 99.04%.
- [``dualcounter``](dualcounter):  adds complexity by running two independent counters
  and comparing them. Still very easy to verify. Friendliness score: 98.18%.
- [``arbiter_prior``](arbiter_prior): An arbiter that grants access based on priorities. 
  Very easy to verify. Friendliness score: 99.45%.
- [``arbiter_rr``](arbiter_rr): An arbiter that grants access in a cyclic order to 
  avoid starvation. Very easy to verify. Friendliness score: 99.05%.
- [``uart_tx``](uart_tx): UART transmitter module. Easy to verify. Friendliness score: 
  98.25%.
- [``fifo_sync``](fifo_sync): A FIFO with a single clock domain. Easy to verify. 
  Friendliness score: 96.12%.
- [``linearinterpolator``](linearinterpolator): A module that calculates intermediate 
  values between two points using linear interpolation. Easy to verify. Friendliness 
  score: 95.47%.
- [``fifo_async``](fifo_async): A FIFO with independent read and write clock domains.
  Easy to verify. Friendliness score: 93.65%.
- [``axi_slave``](axi_slave): A module that interfaces as a slave on the AXI4Lite bus 
  protocol, responding to read and write transactions. OK to verify. Friendliness score: 
  91.34%.
- [``sdram``](sdram): A controller for interfacing with SDRAM. OK to verify.
  Friendliness score: 91.65%.
- [``axi_bridge``](axi_bridge): A bridge module that converts AXI transactions between 
   AXI4 and AXI Lite. Medium to verify. Friendliness score: 62.89%.
- [``axi_master_full``](axi_master_full): A module that initiates AXI4 transactions as a 
  master. Difficult to verify. Friendliness score: 59.97%.
