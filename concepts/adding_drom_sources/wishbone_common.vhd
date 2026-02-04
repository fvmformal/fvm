-- Copyright 2024-2026 Universidad de Sevilla
-- SPDX-License-Identifier: Apache-2.0

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package wishbone_common is

    -- Group signals of Wishbone master interface
    type wb_bus_master_if is
        record
            adr : std_ulogic_vector(31 downto 0);
            dat : std_ulogic_vector(31 downto 0);
            cyc : std_ulogic;
            stb : std_ulogic;
            sel : std_ulogic_vector(3 downto 0);
            we  : std_ulogic;
        end record;

    -- Group signals of a Wishbone slave interface
    type wb_bus_slave_if is
        record
            dat : std_ulogic_vector(31 downto 0);
            ack : std_ulogic;
            err : std_ulogic;
        end record;

end wishbone_common;

package body wishbone_common is

end wishbone_common;
