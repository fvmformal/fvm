module counter #(
    parameter int MAX_COUNT = 128
) (
    input  logic        clk, rst,
    output logic [7:0]  Q
);

    always_ff @(posedge clk or posedge rst)
        if (rst)
            Q <= 0;
        else if (Q == MAX_COUNT)
            Q <= 0;
        else
            Q <= Q + 1;

endmodule
