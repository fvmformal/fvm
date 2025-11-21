-- This design is just a dummy, it has some wishbone ports but the only logic
-- it contains is that of a simple counter

library IEEE;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.wishbone_common.all;

entity wishbone is
    generic ( MAX_COUNT : integer := 128 );
    port ( clk: in  std_logic;
           rst: in  std_logic;
           Master : out wb_bus_master_if;
           Slave  : in  wb_bus_slave_if;
           Q:   out unsigned(7 downto 0)
         );
end wishbone;

architecture behavioral of wishbone is

    signal count:   unsigned(7 downto 0);
    signal n_count: unsigned(7 downto 0);

begin

    Master.dat <= Slave.dat;
    Master.adr <= (others=>'0');

    sinc: process(clk, rst)
    begin
      if (rst='1') then
        count <= (others=>'0');
      elsif (rising_edge(clk)) then
        count <= n_count;
      end if;
    end process;

    comb: process(count)
    begin
      if (count = MAX_COUNT) then
	      n_count <= (others => '0');
      else
	      n_count <= count + 1;
      end if;
    end process;

    Q <= count;

end behavioral;

