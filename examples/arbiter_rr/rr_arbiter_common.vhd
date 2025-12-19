-- Copyright 2024-2025 Universidad de Sevilla
-- SPDX-License-Identifier: Apache-2.0

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package rr_arbiter_common is

    function priority_arbiter(
        requests : std_logic_vector
    ) return std_logic_vector;

    function round_robin_arbiter(
        req : std_logic_vector;
        last_grant : std_logic_vector
    ) return std_logic_vector;
end package rr_arbiter_common;

package body rr_arbiter_common is

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

    function round_robin_arbiter(
        req        : std_logic_vector;
        last_grant : std_logic_vector
    ) return std_logic_vector is
        constant width : integer := req'length;
        variable next_grant : std_logic_vector(req'range) := (others => '0');
        variable start_idx  : integer := -1;
        variable i          : integer;
    begin
        for idx in req'range loop
            if last_grant(idx) = '1' then
                start_idx := idx;
                exit;
            end if;
        end loop;

        if start_idx = -1 then
            return next_grant;
        end if;


        for offset in 1 to width loop
            i := (start_idx - offset + width) mod width;
            if req(i) = '1' then
                next_grant(i) := '1';
                return next_grant;
            end if;
        end loop;

        return next_grant;
    end function;

end package body rr_arbiter_common;