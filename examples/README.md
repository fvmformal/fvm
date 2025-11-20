# Examples

These are some examples that we have done to test the methodology.
Here we order them from easiest to most difficult. We also use the 
friendliness tool from the methodology to check the friendliness score 
of each example, although it may vary depending on the generics.

## Contents

- [``counter``](counter): a simple up counter. Friendliness score: 99.30%.
- [``dualcounter``](dualcounter): A dualcounter. Friendliness score: 98.22%.
- [``arbiter_prior``](arbiter_prior): A priority arbiter. Friendliness score: 94.94%.
- [``arbiter_rr``](arbiter_rr): A round robin arbiter. Friendliness score: 95.61%.
- [``uart_tx``](uart_tx): UART transmitter. Friendliness score: 98.14%.
- [``axi_slave``](axi_slave): AXI-4 lite slave. Friendliness score: 90.86%.
- [``sdram``](sdram): SDRAM controller. OK to verify. Friendliness score: 92.34%.
- [``linearinterpolator``](linearinterpolator): A linear interpolator that interpolates
  during 12 cycles. Friendliness score: 98.19%.
- [``fifo_sync``](fifo_sync): A synchronous FIFO. Friendliness score: 80.59%
  (It changes a lot depending on the selected configuration, current result for FIFO 32x16).
- [``div32``](axi_bridge): A divider with a 64-bit dividend and 32-bit divisor that
  takes 36 cycles to divide. Friendliness score: 93.81%.
- [``fifo_async``](fifo_async): An asynchronous FIFO. Friendliness score: 75.16% (It changes
  a lot depending on the selected configuration, current result for FIFO 32x16).
- [``ipv6``](ipv6): An IPv6 transceiver. Friendliness score: 66.16%