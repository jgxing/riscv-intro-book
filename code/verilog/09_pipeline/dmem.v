module dmem (
    input  wire        clk,
    input  wire [31:0] addr,
    input  wire        we,
    input  wire [2:0]  funct3,
    input  wire [31:0] wdata,
    output reg  [31:0] rdata
);

    localparam [31:0] BASE  = 32'h10000000;
    localparam        IDX_W = 12;
    localparam        BYTES = 1 << IDX_W;

    reg [7:0] mem [0:BYTES-1];

    wire [31:0] offset     = addr - BASE;
    wire [IDX_W-1:0] byte_addr = offset[IDX_W-1:0];

    reg [3:0] be;
    always @(*) begin
        case (funct3)
            3'b000: be = 4'b0001;
            3'b001: be = 4'b0011;
            3'b010: be = 4'b1111;
            default: be = 4'b0000;
        endcase
    end

    integer i;
    always @(posedge clk) begin
        if (we) begin
            for (i = 0; i < 4; i = i + 1)
                if (be[i])
                    mem[byte_addr + i] <= wdata[i*8 +: 8];
        end
    end

    wire [7:0] b0 = (addr >= BASE) ? mem[byte_addr]     : 8'b0;
    wire [7:0] b1 = (addr >= BASE) ? mem[byte_addr + 1] : 8'b0;
    wire [7:0] b2 = (addr >= BASE) ? mem[byte_addr + 2] : 8'b0;
    wire [7:0] b3 = (addr >= BASE) ? mem[byte_addr + 3] : 8'b0;

    always @(*) begin
        case (funct3)
            3'b000: rdata = {{24{b0[7]}}, b0};
            3'b001: rdata = {{16{b1[7]}}, b1, b0};
            3'b010: rdata = {b3, b2, b1, b0};
            3'b100: rdata = {24'b0, b0};
            3'b101: rdata = {16'b0, b1, b0};
            default: rdata = 32'b0;
        endcase
    end

endmodule
