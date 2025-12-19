-- Copyright 2024-2025 Universidad de Sevilla
-- SPDX-License-Identifier: Apache-2.0

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package arbiter_prior_common is

    function priority_arbiter(
        requests : std_logic_vector
    ) return std_logic_vector;

end package arbiter_prior_common;

package body arbiter_prior_common is

    function priority_arbiter(
        requests : std_logic_vector
    ) return std_logic_vector is
        variable grant : std_logic_vector(requests'range) := (others => '0');
        variable i     : integer;
    begin
        for i in requests'left downto requests'right loop
            if requests(i) = '1' then
                grant(i) := '1';
                exit;
            end if;
        end loop;
        return grant;
    end function;

end package body arbiter_prior_common;