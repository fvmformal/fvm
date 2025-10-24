module counter #(
    parameter int MAX_COUNT = 128
) (
    input  logic        clk,
    input  logic        rst,
    output logic [7:0]  Q
);

    logic [7:0] count;
    logic [7:0] p_count;

    always_ff @(posedge clk or posedge rst) begin
        if (rst)
            count <= 8'd0;
        else
            count <= p_count;
    end

    always_comb begin
        if (count == MAX_COUNT)
            p_count = 8'd0;
        else
            p_count = count + 1;
    end

    assign Q = count;

endmodule
