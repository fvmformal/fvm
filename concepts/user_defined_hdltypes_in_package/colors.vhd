-- Copyright 2024-2026 Universidad de Sevilla
-- SPDX-License-Identifier: Apache-2.0

library IEEE;
use ieee.std_logic_1164.all;
use work.colors_common.all;

entity colors is
    generic ( MAX_COUNT : integer := 128 );
    port ( clk: in  std_ulogic;
           rst: in  std_ulogic;
           colorvect:   out std_ulogic_vector(6 downto 0)
         );
end colors;

architecture behavioral of colors is

    signal color, n_color: color_t;

begin

    colorvect(0) <= '1' when color = red else '0';
    colorvect(1) <= '1' when color = orange else '0';
    colorvect(2) <= '1' when color = yellow else '0';
    colorvect(3) <= '1' when color = green else '0';
    colorvect(4) <= '1' when color = blue else '0';
    colorvect(5) <= '1' when color = indigo else '0';
    colorvect(6) <= '1' when color = violet else '0';

    sinc: process(clk, rst)
    begin
      if (rst='1') then
        color <= red;
      elsif (rising_edge(clk)) then
        color <= n_color;
      end if;
    end process;

    comb: process(color)
    begin
      case color is
        when red =>
          n_color <= orange;
        when orange =>
          n_color <= yellow;
        when yellow =>
          n_color <= green;
        when green =>
          n_color <= blue;
        when blue =>
          n_color <= indigo;
        when indigo =>
          n_color <= violet;
        when violet =>
          n_color <= red;
      end case;
    end process;

end behavioral;
