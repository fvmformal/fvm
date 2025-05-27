library ieee;
use ieee.std_logic_1164.all;

-- Synchronizer to pass single-bit signals between two clock domains
entity synchronizer is
    generic (
        STAGES    : positive   := 2;   -- Number of flip-flops (typically 2 or 3)
        RST_VALUE : std_ulogic := '0'  -- Reset value for the flip-flops
    );
    port (
        input  : in  std_ulogic;  -- input, asynchronous with respect to clk
        rst    : in  std_ulogic;  -- asyncronous reset, active high
        clk    : in  std_ulogic;  -- clock with which to synchronize input
        output : out std_ulogic   -- output signal, synchronous with clk
    );
end synchronizer;

architecture synchronizer_arch of synchronizer is

    signal reg, n_reg : std_ulogic_vector(STAGES-1 downto 0);

begin

    -- Commented out the following assertion because we want to see if we can
    -- find issues when STAGES=1
    --
    -- A synchronizer needs at least two flip-flops
    --assert STAGES >= 2
        --report synchronizer'PATH_NAME & " bad value for STAGES (" &  -- not supported by propcheck :(
    --    report "synchronizer:" & " bad value for STAGES (" &
    --           integer'IMAGE(STAGES) & "), should be at least 2"
    --    severity failure;

    -- Input enters the LSB of reg, then gets shifted towards output once per clk cycle
    n_reg <= reg(reg'HIGH-1 downto reg'LOW) & input;

    -- Output is the most significant bit (the one which has crossed more stages)
    output <= reg(reg'HIGH);

    -- All flip-flops capture data on the rising edge of clk
    sync: process(rst, clk)
    begin
        if rst = '1' then
            reg <= (others => RST_VALUE);
        elsif rising_edge(clk) then
            reg <= n_reg;
        end if;
    end process;

end synchronizer_arch;
