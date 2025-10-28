module counter #(
    parameter MAX_COUNT = 128
) (
    input  wire clk,
    input  wire rst,
    output reg [7:0] Q
);

always @(posedge clk or posedge rst) begin
    if (rst)
        Q <= 8'd0;
    else if (Q == MAX_COUNT)
        Q <= 8'd0;
    else
        Q <= Q + 1;
end

endmodule
