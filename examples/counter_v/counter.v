module counter #(
    parameter MAX_COUNT = 128
) (
    input  wire        clk,
    input  wire        rst,
    output reg  [7:0]  Q
);

    reg [7:0] count;
    reg [7:0] p_count;

    always @(posedge clk or posedge rst) begin
        if (rst)
            count <= 8'd0;
        else
            count <= p_count;
    end

    always @(*) begin
        if (count == MAX_COUNT)
            p_count = 8'd0;
        else
            p_count = count + 1;
    end

    always @(*) begin
        Q = count;
    end

endmodule
