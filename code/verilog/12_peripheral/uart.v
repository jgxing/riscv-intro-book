module uart (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [31:0] addr,
    input  wire        we,
    input  wire [31:0] wdata,
    input  wire [7:0]  rx_i,
    input  wire        rx_valid_i,
    output reg  [7:0]  tx_o,
    output reg         tx_valid_o,
    output reg  [31:0] rdata
);

    localparam [31:0] DATA_ADDR  = 32'hffff0030;
    localparam [31:0] STAT_ADDR  = 32'hffff0034;

    localparam [31:0] LSR_DR    = 32'h00000001;  // 接收数据就绪
    localparam [31:0] LSR_THRE  = 32'h00000020;  // 发送保持寄存器空

    wire data_sel = (addr == DATA_ADDR);
    wire stat_sel = (addr == STAT_ADDR);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_o        <= 8'b0;
            tx_valid_o  <= 1'b0;
        end else begin
            tx_valid_o <= 1'b0;
            if (we && data_sel) begin
                tx_o       <= wdata[7:0];
                tx_valid_o <= 1'b1;
            end
        end
    end

    always @(*) begin
        if (stat_sel)
            rdata = LSR_THRE | (rx_valid_i ? LSR_DR : 32'b0);
        else if (data_sel)
            rdata = {24'b0, rx_i};
        else
            rdata = 32'b0;
    end

endmodule
