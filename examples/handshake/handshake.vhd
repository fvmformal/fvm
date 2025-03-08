library ieee;
use ieee.std_logic_1164.all;

-- Handshaker to pass multi-bit signals between two clock domains
--
-- Each interface has its own reset: we can't have the same reset for both,
-- because even asynchronous resets must be synchronously deasserted for the
-- circuits to work without issues. If we try a single reset for both
-- interfaces, questa CDC/RDC very rightly complains
entity handshake is
    generic (
        DATA_WIDTH : positive   := 8;   -- Width of data to pass 
        STAGES     : positive   := 2;   -- Number of flip-flops of the internal synchronizers
        RST_VALUE  : std_ulogic := '0'  -- Reset value for the synchronizer FFs
    );
    port (
        -- A: writing (requesting) interface
        a_clk      : in  std_ulogic;  -- clock of the requesting clock domain
        a_rst      : in  std_ulogic;  -- reset of the requesting clock domain
        a_data_in  : in  std_ulogic_vector(DATA_WIDTH-1 downto 0);  -- Data from A to B
        a_req_in   : in  std_ulogic;  -- request from A
        a_ack_out  : out std_ulogic;  -- acknowledge from B
        -- B: reading (acknowledging) interface
        b_clk      : in  std_ulogic;  -- clock of the acknowledging clock domain
        b_rst      : in  std_ulogic;  -- reset of the acknowledging clock domain
        b_data_out : out std_ulogic_vector(DATA_WIDTH-1 downto 0);  -- Data from A to B
        b_ack_in   : in  std_ulogic;  -- acknowledge from B
        b_req_out  : out std_ulogic   -- request from A
    );
end handshake;

architecture handshake_arch of handshake is

begin

    -- Data passes 'as is' between clock domains, but if:
    --   * B only samples it after seeing b_req_out, and
    --   * A only changes it after seeing a_ack_out, then
    -- B should read the data A intended to send (the data should be stable)
    --
    -- Actual, detailed timeline would be:
    --   1. A changes a_data_in
    --   2. A changes a_req_in (*after* the previous step, never at the same time)
    --   3. B sees b_req_out: B can read b_data_out because data is stable
    --   4. B changes b_ack_in (this could probably be simultaneous to the previous step)
    --   5. A sees b_ack_out, so it can change the data (goes to step 1.)
    b_data_out <= a_data_in;

    -- Pass requests from domain A to domain B
    sync_req_from_a_to_b: entity work.synchronizer
      generic map (
        STAGES => STAGES,
        RST_VALUE => RST_VALUE
      )
      port map (
        input  => a_req_in,
        rst    => b_rst,
        clk    => b_clk,
        output => b_req_out
      );

    -- Pass acknowledgement from domain B to domain A
    sync_ack_from_b_to_a: entity work.synchronizer
      generic map (
        STAGES => STAGES,
        RST_VALUE => RST_VALUE
      )
      port map (
        input  => b_ack_in,
        rst    => a_rst,
        clk    => a_clk,
        output => a_ack_out
      );

end handshake_arch;
