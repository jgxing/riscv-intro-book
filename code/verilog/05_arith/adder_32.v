module adder_32 (
    input  wire [31:0] a,
    input  wire [31:0] b,
    input  wire        cin,
    output wire [31:0] sum,
    output wire        cout
);

    wire [31:0] carry;

    genvar i;
    generate
        for (i = 0; i < 32; i = i + 1) begin : g_bit
            if (i == 0) begin : g_first
                full_adder u_fa (
                    .a    (a[0]),
                    .b    (b[0]),
                    .cin  (cin),
                    .sum  (sum[0]),
                    .cout (carry[0])
                );
            end else begin : g_rest
                full_adder u_fa (
                    .a    (a[i]),
                    .b    (b[i]),
                    .cin  (carry[i-1]),
                    .sum  (sum[i]),
                    .cout (carry[i])
                );
            end
        end
    endgenerate

    assign cout = carry[31];

endmodule
