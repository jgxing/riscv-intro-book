module gpio (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [31:0] addr,
    input  wire        we,
    input  wire [31:0] wdata,
    input  wire [7:0]  switch_i,
    output reg  [7:0]  led_o,
    output reg  [31:0] rdata
);

    localparam [31:0] LED_ADDR    = 32'hffff0010;
    localparam [31:0] SWITCH_ADDR = 32'hffff0020;

    wire led_sel    = (addr == LED_ADDR);
    wire switch_sel = (addr == SWITCH_ADDR);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            led_o <= 8'b0;
        else if (we && led_sel)
            led_o <= wdata[7:0];
    end

    always @(*) begin
        rdata = switch_sel ? {24'b0, switch_i} : 32'b0;
    end

endmodule
