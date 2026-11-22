module timer (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [31:0] addr,
    output reg  [31:0] rdata
);

    localparam [31:0] MTIME_LO = 32'hffff0000;
    localparam [31:0] MTIME_HI = 32'hffff0004;

    reg [63:0] count;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= 64'b0;
        else
            count <= count + 64'd1;
    end

    always @(*) begin
        if (addr == MTIME_LO)
            rdata = count[31:0];
        else if (addr == MTIME_HI)
            rdata = count[63:32];
        else
            rdata = 32'b0;
    end

endmodule
