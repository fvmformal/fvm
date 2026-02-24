-- Copyright 2024-2026 Universidad de Sevilla
-- SPDX-License-Identifier: Apache-2.0

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.edc_common.all;

package interpolator_common is
    type interpolator_input_tran is record
        infr : complex10;  
        supr : complex10;  
    end record;

    type interpolator_output_tran is array (0 to 11) of complex10;

    function interpolator_predict(
        input_tran : interpolator_input_tran
    ) return interpolator_output_tran;
end package interpolator_common;

package body interpolator_common is

    function interpolator_predict(
        input_tran : interpolator_input_tran
    ) return interpolator_output_tran is
        variable output_tran : interpolator_output_tran;
        variable infr_re, infr_im : integer;
        variable supr_re, supr_im : integer;
        variable num   : integer;
        variable tmp   : integer;
        variable tmp_signed : signed(15 downto 0);
    begin
        infr_re := to_integer(input_tran.infr.re);
        infr_im := to_integer(input_tran.infr.im);
        supr_re := to_integer(input_tran.supr.re);
        supr_im := to_integer(input_tran.supr.im);

        for i in 0 to 11 loop
            num := (infr_re * (12 - i)) + (supr_re * i);
            -- if so that the integer is truncated as signed
            if num < 0 then
                tmp := (num * 3 - 48 + 1) / 48;
            else
                tmp := (num * 3) / 48;
            end if;
            output_tran(i).re := to_signed(tmp, 10);
            num := (infr_im * (12 - i)) + (supr_im * i);
            -- if so that the integer is truncated as signed
            if num < 0 then
                tmp := (num * 3 - 48 + 1) / 48;
            else
                tmp := (num * 3) / 48;
            end if;
            output_tran(i).im := to_signed(tmp, 10);
        end loop;

        return output_tran;
    end function;
    
end package body interpolator_common;
