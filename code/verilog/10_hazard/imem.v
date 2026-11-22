module imem (
    input  wire [31:0] addr,
    output reg  [31:0] instr
);

    localparam [31:0] BASE   = 32'h00400000;
    localparam        IDX_W  = 10;
    localparam        DEPTH  = 1 << IDX_W;

    reg [31:0] mem [0:DEPTH-1];

    initial begin
        $readmemh("code.hex", mem);
    end

    wire [31:0] offset = addr - BASE;
    wire [IDX_W-1:0] idx = offset[IDX_W+1:2];

    always @(*) begin
        if (addr >= BASE && offset < DEPTH * 4)
            instr = mem[idx];
        else
            instr = 32'h00000013;
    end

endmodule
