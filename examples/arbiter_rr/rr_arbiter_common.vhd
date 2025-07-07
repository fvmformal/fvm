library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package rr_arbiter_common is

    function round_robin(
        req: std_logic_vector(3 downto 0); last_grant: std_logic_vector(3 downto 0)) 
    return std_logic_vector;
    
end package rr_arbiter_common;

package body rr_arbiter_common is

-- This function simulates the round_robin algorithm.
-- This is not the optimal way to do the round robin function,
-- but this way is easier to understand what the function does
function round_robin(req: std_logic_vector(3 downto 0); last_grant: std_logic_vector(3 downto 0)) return std_logic_vector is
    variable next_grant: std_logic_vector(3 downto 0);  
begin

    if last_grant = "1000" then
        if req(2) = '1' then
            next_grant := "0100";  
        elsif req(1) = '1' then
            next_grant := "0010";  
        elsif req(0) = '1' then
            next_grant := "0001";  
        elsif req(3) = '1' then
            next_grant := "1000";  
        end if;

    elsif last_grant = "0100" then
        if req(1) = '1' then
            next_grant := "0010";  
        elsif req(0) = '1' then
            next_grant := "0001";  
        elsif req(3) = '1' then
            next_grant := "1000";  
        elsif req(2) = '1' then
            next_grant := "0100"; 
        end if;

    elsif last_grant = "0010" then
        if req(0) = '1' then
            next_grant := "0001"; 
        elsif req(3) = '1' then
            next_grant := "1000"; 
        elsif req(2) = '1' then
            next_grant := "0100"; 
        elsif req(1) = '1' then
            next_grant := "0010"; 
        end if;

    elsif last_grant = "0001" then
        if req(3) = '1' then
            next_grant := "1000";  
        elsif req(2) = '1' then
            next_grant := "0100"; 
        elsif req(1) = '1' then
            next_grant := "0010"; 
        elsif req(0) = '1' then
            next_grant := "0001";  
        end if;

    else 
        next_grant := "0000"; 
    end if;

    return next_grant;
end function;
    
end package body rr_arbiter_common;
