-- Copyright 2024-2025 Universidad de Sevilla
-- SPDX-License-Identifier: Apache-2.0

library ieee;
use ieee.std_logic_1164.all;

package colors_common is

  type color_t is (red, orange, yellow, green, blue, indigo, violet);

  type color_record is
    record
      a : color_t;
      b : color_t;
      c : color_t;
    end record;

  function onehot(constant vect : std_ulogic_vector(6 downto 0)) return boolean;

end package;

package body colors_common is

  -- Helper function to check if a color vector is onehot
  function onehot(constant vect : std_ulogic_vector(6 downto 0)) return boolean is
    variable ret : boolean := true;
  begin
    case vect is
      when "0000001" => ret := true;
      when "0000010" => ret := true;
      when "0000100" => ret := true;
      when "0001000" => ret := true;
      when "0010000" => ret := true;
      when "0100000" => ret := true;
      when "1000000" => ret := true;
      when others => ret := false;
    end case;
    return ret;
  end function;

end package body;
